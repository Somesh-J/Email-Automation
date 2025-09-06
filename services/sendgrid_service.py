"""
SendGrid service for sending emails
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import httpx
from datetime import datetime

from core.config import settings
from core.logger import email_logger

logger = logging.getLogger(__name__)

class SendGridService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SendGrid client"""
        try:
            if settings.SENDGRID_API_KEY:
                self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
                logger.info("SendGrid client initialized")
            else:
                logger.warning("SendGrid API key not provided")
        except Exception as e:
            logger.error(f"Error initializing SendGrid client: {e}")
    
    async def send_email(self, 
                        to_email: str,
                        subject: str,
                        content: str,
                        from_email: Optional[str] = None,
                        from_name: Optional[str] = None,
                        content_type: str = "text/plain",
                        reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Send single email"""
        
        if not self.client:
            return {
                "success": False,
                "error": "SendGrid client not initialized"
            }
        
        try:
            # Prepare email addresses
            from_email = from_email or settings.FROM_EMAIL
            from_name = from_name or settings.FROM_NAME
            
            # Create mail object
            mail = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=content if content_type == "text/plain" else None,
                html_content=content if content_type == "text/html" else None
            )
            
            # Set reply-to if provided
            if reply_to:
                mail.reply_to = Email(reply_to)
            
            # Send email
            response = await asyncio.to_thread(self.client.send, mail)
            
            # Check response
            if response.status_code in [200, 202]:
                email_logger.log_email_replied(to_email, subject, "sendgrid")
                return {
                    "success": True,
                    "message_id": response.headers.get('X-Message-Id'),
                    "status_code": response.status_code
                }
            else:
                logger.error(f"SendGrid send failed: {response.status_code} - {response.body}")
                return {
                    "success": False,
                    "error": f"SendGrid error: {response.status_code}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            email_logger.log_email_failed(to_email, subject, str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_emails(self, 
                             recipients: List[Dict[str, Any]],
                             subject: str,
                             content: str,
                             from_email: Optional[str] = None,
                             from_name: Optional[str] = None,
                             content_type: str = "text/plain",
                             batch_size: int = 10,
                             delay: float = 1.0) -> Dict[str, Any]:
        """Send bulk emails with rate limiting"""
        
        if not self.client:
            return {
                "success": False,
                "error": "SendGrid client not initialized",
                "sent": 0,
                "failed": 0
            }
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        # Process recipients in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            # Send emails in current batch
            batch_tasks = []
            for recipient in batch:
                if isinstance(recipient, str):
                    to_email = recipient
                    personalization = {}
                else:
                    to_email = recipient.get('email', '')
                    personalization = recipient.get('data', {})
                
                if not to_email:
                    failed_count += 1
                    continue
                
                # Personalize content if data provided
                personalized_subject = subject
                personalized_content = content
                
                if personalization:
                    try:
                        personalized_subject = subject.format(**personalization)
                        personalized_content = content.format(**personalization)
                    except KeyError as e:
                        logger.warning(f"Personalization key missing: {e}")
                
                # Create send task
                task = self.send_email(
                    to_email=to_email,
                    subject=personalized_subject,
                    content=personalized_content,
                    from_email=from_email,
                    from_name=from_name,
                    content_type=content_type
                )
                batch_tasks.append(task)
            
            # Execute batch
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        errors.append(str(result))
                    elif result.get('success'):
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append(result.get('error', 'Unknown error'))
            
            # Delay between batches (except for last batch)
            if i + batch_size < len(recipients):
                await asyncio.sleep(delay)
        
        email_logger.log_bulk_email_complete(
            job_id=f"bulk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            sent=sent_count,
            failed=failed_count
        )
        
        return {
            "success": failed_count == 0,
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients),
            "errors": errors[:10]  # Limit error list
        }
    
    async def send_template_email(self,
                                to_email: str,
                                template_id: str,
                                dynamic_data: Dict[str, Any],
                                from_email: Optional[str] = None,
                                from_name: Optional[str] = None) -> Dict[str, Any]:
        """Send email using SendGrid template"""
        
        if not self.client:
            return {
                "success": False,
                "error": "SendGrid client not initialized"
            }
        
        try:
            from_email = from_email or settings.FROM_EMAIL
            from_name = from_name or settings.FROM_NAME
            
            # Create mail object with template
            mail = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email)
            )
            
            # Set template ID
            mail.template_id = template_id
            
            # Add dynamic data
            if dynamic_data:
                mail.dynamic_template_data = dynamic_data
            
            # Send email
            response = await asyncio.to_thread(self.client.send, mail)
            
            if response.status_code in [200, 202]:
                return {
                    "success": True,
                    "message_id": response.headers.get('X-Message-Id'),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"SendGrid error: {response.status_code}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_email_stats(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get email statistics from SendGrid"""
        
        if not self.client:
            return {
                "success": False,
                "error": "SendGrid client not initialized"
            }
        
        try:
            # Use SendGrid Stats API
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Bearer {settings.SENDGRID_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                url = f"https://api.sendgrid.com/v3/stats"
                params = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'aggregated_by': 'day'
                }
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "stats": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email address using SendGrid"""
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Bearer {settings.SENDGRID_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                url = "https://api.sendgrid.com/v3/validations/email"
                data = {"email": email}
                
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "valid": result.get('result', {}).get('verdict') == 'Valid',
                        "details": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Validation API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error validating email: {e}")
            return {
                "success": False,
                "error": str(e),
                "valid": False
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of SendGrid service"""
        
        if not self.client:
            return {
                "status": "unhealthy",
                "error": "SendGrid client not initialized"
            }
        
        try:
            # Test API connectivity
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Bearer {settings.SENDGRID_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                url = "https://api.sendgrid.com/v3/user/profile"
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    profile = response.json()
                    return {
                        "status": "healthy",
                        "api_accessible": True,
                        "account": profile.get('username', 'Unknown')
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "api_accessible": False,
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error in SendGrid health check: {e}")
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e)
            }

# Create SendGrid service instance
sendgrid_service = SendGridService()
