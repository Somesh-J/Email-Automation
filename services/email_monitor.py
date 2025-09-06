"""
Email monitoring service for automated email processing
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from .email_service import email_service
from .ai_service import ai_service
from .sendgrid_service import sendgrid_service
from core.config import settings
from core.database import database_manager
from core.logger import email_logger

logger = logging.getLogger(__name__)

class EmailMonitorService:
    """Service for monitoring and processing emails automatically"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = settings.EMAIL_CHECK_INTERVAL
        self.task = None
        self.last_check = None
        self.processed_emails = set()
        self.allowed_domains = set(settings.DEFAULT_ALLOWED_DOMAINS)
        self.stats = {
            'emails_processed': 0,
            'replies_sent': 0,
            'errors': 0,
            'last_error': None
        }
    
    async def start(self):
        """Start email monitoring"""
        if self.is_running:
            logger.warning("Email monitoring is already running")
            return
        
        try:
            self.is_running = True
            self.task = asyncio.create_task(self._monitor_loop())
            email_logger.log_monitoring_start("email_monitor")
            logger.info("Email monitoring started")
            
            # Update monitoring status in database
            await self._update_monitoring_status(True)
            
        except Exception as e:
            logger.error(f"Error starting email monitoring: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop email monitoring"""
        if not self.is_running:
            logger.warning("Email monitoring is not running")
            return
        
        try:
            self.is_running = False
            
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            email_logger.log_monitoring_stop("email_monitor")
            logger.info("Email monitoring stopped")
            
            # Update monitoring status in database
            await self._update_monitoring_status(False)
            
        except Exception as e:
            logger.error(f"Error stopping email monitoring: {e}")
    
    async def restart(self):
        """Restart email monitoring"""
        await self.stop()
        await asyncio.sleep(1)  # Brief pause
        await self.start()
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Email monitoring loop started with {self.check_interval}s interval")
        
        while self.is_running:
            try:
                await self._check_for_new_emails()
                self.last_check = datetime.utcnow()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Email monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
                
                # Continue monitoring after error
                await asyncio.sleep(min(self.check_interval, 60))
    
    async def _check_for_new_emails(self):
        """Check for new emails and process them"""
        try:
            # Get unread emails
            unread_emails = await email_service.get_unread_emails()
            
            if not unread_emails:
                return
            
            logger.info(f"Found {len(unread_emails)} unread emails")
            
            # Process each email
            for email_data in unread_emails:
                try:
                    await self._process_email(email_data)
                    self.stats['emails_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('id')}: {e}")
                    self.stats['errors'] += 1
                    
                    # Log error to database
                    await self._log_email_error(email_data, str(e))
            
        except Exception as e:
            logger.error(f"Error checking for new emails: {e}")
            raise
    
    async def _process_email(self, email_data: Dict[str, Any]):
        """Process individual email"""
        email_id = email_data.get('id')
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        domain = email_data.get('domain', '')
        
        # Skip if already processed
        if email_id in self.processed_emails:
            return
        
        self.processed_emails.add(email_id)
        
        # Log email receipt
        email_logger.log_email_received(sender, subject, email_id)
        
        # Log to database
        await database_manager.log_email({
            'email_id': email_id,
            'sender': sender,
            'subject': subject,
            'body': body,
            'action': 'received',
            'metadata': {'domain': domain}
        })
        
        # Check if domain is allowed for auto-reply
        if not await self._is_domain_allowed(domain):
            logger.info(f"Domain {domain} not allowed for auto-reply")
            email_logger.log_domain_check(domain, False)
            return
        
        email_logger.log_domain_check(domain, True)
        
        # Check if we should auto-reply
        if not settings.ENABLE_AUTO_REPLY:
            logger.info("Auto-reply is disabled")
            return
        
        # Check reply history to avoid spamming
        if await self._should_skip_reply(sender):
            logger.info(f"Skipping reply to {sender} (recent reply exists)")
            return
        
        # Generate AI reply
        try:
            ai_reply = await ai_service.generate_reply(subject, body, sender)
            
            if not ai_reply:
                logger.warning(f"Could not generate AI reply for email from {sender}")
                return
            
            # Send reply
            send_result = await sendgrid_service.send_email(
                to_email=sender,
                subject=f"Re: {subject}" if not subject.startswith('Re:') else subject,
                content=ai_reply,
                content_type="text/plain"
            )
            
            if send_result.get('success'):
                logger.info(f"Auto-reply sent to {sender}")
                self.stats['replies_sent'] += 1
                
                # Log reply to database
                await database_manager.log_email({
                    'email_id': email_id,
                    'sender': settings.FROM_EMAIL,
                    'recipient': sender,
                    'subject': f"Re: {subject}",
                    'body': ai_reply,
                    'action': 'auto_replied',
                    'reply_type': 'auto',
                    'status': 'sent',
                    'metadata': {
                        'original_email_id': email_id,
                        'message_id': send_result.get('message_id')
                    }
                })
                
                # Mark original email as read
                await email_service.mark_as_read(email_id)
                
            else:
                logger.error(f"Failed to send auto-reply to {sender}: {send_result.get('error')}")
                await self._log_reply_error(email_data, send_result.get('error', 'Unknown error'))
                
        except Exception as e:
            logger.error(f"Error generating/sending auto-reply for {sender}: {e}")
            await self._log_reply_error(email_data, str(e))
    
    async def _is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed for auto-reply"""
        try:
            # Check in-memory cache first
            if domain in self.allowed_domains:
                return True
            
            # Check database
            domains = await database_manager.get_domains(is_allowed=True)
            allowed_domains = {d['domain'] for d in domains}
            
            # Update cache
            self.allowed_domains = allowed_domains
            
            return domain in allowed_domains
            
        except Exception as e:
            logger.error(f"Error checking domain {domain}: {e}")
            # Fallback to default domains
            return domain in settings.DEFAULT_ALLOWED_DOMAINS
    
    async def _should_skip_reply(self, sender: str, hours: int = 24) -> bool:
        """Check if we should skip replying to avoid spam"""
        try:
            # Check database for recent replies to this sender
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=hours)
            
            recent_logs = await database_manager.get_email_logs(
                limit=1,
                sender=settings.FROM_EMAIL,  # Our replies
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter for replies to this specific sender
            recent_replies = [
                log for log in recent_logs
                if log.get('recipient') == sender and log.get('action') == 'auto_replied'
            ]
            
            return len(recent_replies) > 0
            
        except Exception as e:
            logger.error(f"Error checking reply history for {sender}: {e}")
            # Err on the side of not spamming
            return True
    
    async def _log_email_error(self, email_data: Dict[str, Any], error: str):
        """Log email processing error"""
        try:
            await database_manager.log_email({
                'email_id': email_data.get('id'),
                'sender': email_data.get('sender'),
                'subject': email_data.get('subject'),
                'body': email_data.get('body'),
                'action': 'processing_error',
                'status': 'failed',
                'error_message': error,
                'metadata': {'processing_error': True}
            })
        except Exception as e:
            logger.error(f"Error logging email error: {e}")
    
    async def _log_reply_error(self, email_data: Dict[str, Any], error: str):
        """Log reply sending error"""
        try:
            await database_manager.log_email({
                'email_id': email_data.get('id'),
                'sender': settings.FROM_EMAIL,
                'recipient': email_data.get('sender'),
                'subject': f"Re: {email_data.get('subject', '')}",
                'action': 'auto_reply_failed',
                'reply_type': 'auto',
                'status': 'failed',
                'error_message': error,
                'metadata': {'original_email_id': email_data.get('id')}
            })
        except Exception as e:
            logger.error(f"Error logging reply error: {e}")
    
    async def _update_monitoring_status(self, is_active: bool):
        """Update monitoring status in database"""
        try:
            # This would update the monitoring_status table
            # Implementation depends on database structure
            pass
        except Exception as e:
            logger.error(f"Error updating monitoring status: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'processed_emails_count': len(self.processed_emails),
            'allowed_domains_count': len(self.allowed_domains),
            'stats': self.stats.copy()
        }
    
    async def update_settings(self, **kwargs):
        """Update monitoring settings"""
        if 'check_interval' in kwargs:
            self.check_interval = max(10, int(kwargs['check_interval']))  # Min 10 seconds
            logger.info(f"Check interval updated to {self.check_interval}s")
        
        if 'allowed_domains' in kwargs:
            self.allowed_domains = set(kwargs['allowed_domains'])
            logger.info(f"Allowed domains updated: {self.allowed_domains}")
    
    async def force_check(self) -> Dict[str, Any]:
        """Force immediate email check"""
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Monitoring is not running'
                }
            
            await self._check_for_new_emails()
            
            return {
                'success': True,
                'message': 'Email check completed',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in forced email check: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of monitoring service"""
        try:
            # Check email service health
            email_health = await email_service.health_check()
            
            # Check AI service health
            ai_health = await ai_service.health_check()
            
            # Check SendGrid health
            sendgrid_health = await sendgrid_service.health_check()
            
            # Overall health
            all_healthy = all([
                email_health.get('status') == 'healthy',
                ai_health.get('status') == 'healthy',
                sendgrid_health.get('status') == 'healthy'
            ])
            
            return {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'is_running': self.is_running,
                'services': {
                    'email': email_health,
                    'ai': ai_health,
                    'sendgrid': sendgrid_health
                },
                'stats': self.stats,
                'last_check': self.last_check.isoformat() if self.last_check else None
            }
            
        except Exception as e:
            logger.error(f"Error in monitoring health check: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'is_running': self.is_running
            }

# Create email monitor service instance
email_monitor_service = EmailMonitorService()
