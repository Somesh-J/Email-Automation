"""
Email service for handling IMAP operations and email processing
"""

import asyncio
import aioimaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import re

from core.config import settings, EMAIL_PROVIDERS
from core.logger import email_logger

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.imap_client = None
        self.connection_pool = {}
        self.last_connection_time = None
        self.connection_timeout = 300  # 5 minutes
        
    async def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            if self.imap_client and await self._test_connection():
                return True
                
            # Create new connection
            self.imap_client = aioimaplib.IMAP4_SSL(
                host=settings.IMAP_SERVER,
                port=settings.IMAP_PORT
            )
            
            await self.imap_client.wait_hello_from_server()
            
            # Login
            login_response = await self.imap_client.login(
                settings.IMAP_USERNAME,
                settings.IMAP_PASSWORD
            )
            
            if login_response.result != 'OK':
                logger.error(f"IMAP login failed: {login_response}")
                return False
            
            self.last_connection_time = datetime.utcnow()
            logger.info("IMAP connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to IMAP server: {e}")
            self.imap_client = None
            return False
    
    async def disconnect(self):
        """Disconnect from IMAP server"""
        if self.imap_client:
            try:
                await self.imap_client.logout()
            except Exception as e:
                logger.error(f"Error disconnecting from IMAP: {e}")
            finally:
                self.imap_client = None
                self.last_connection_time = None
    
    async def _test_connection(self) -> bool:
        """Test if current connection is still valid"""
        if not self.imap_client:
            return False
            
        try:
            response = await self.imap_client.noop()
            return response.result == 'OK'
        except Exception:
            return False
    
    async def _ensure_connection(self) -> bool:
        """Ensure we have a valid connection"""
        if self.last_connection_time:
            time_since_connection = datetime.utcnow() - self.last_connection_time
            if time_since_connection.total_seconds() > self.connection_timeout:
                await self.disconnect()
        
        if not self.imap_client or not await self._test_connection():
            return await self.connect()
        
        return True
    
    async def get_mailboxes(self) -> List[str]:
        """Get list of available mailboxes"""
        if not await self._ensure_connection():
            return []
        
        try:
            response = await self.imap_client.list()
            if response.result != 'OK':
                return ['INBOX']
            
            mailboxes = []
            for line in response.lines:
                # Parse mailbox name from LIST response
                parts = line.decode().split('"')
                if len(parts) >= 3:
                    mailbox_name = parts[-2]
                    mailboxes.append(mailbox_name)
            
            return mailboxes or ['INBOX']
            
        except Exception as e:
            logger.error(f"Error getting mailboxes: {e}")
            return ['INBOX']
    
    async def select_mailbox(self, mailbox: str = 'INBOX') -> bool:
        """Select a mailbox"""
        if not await self._ensure_connection():
            return False
        
        try:
            response = await self.imap_client.select(mailbox)
            return response.result == 'OK'
        except Exception as e:
            logger.error(f"Error selecting mailbox {mailbox}: {e}")
            return False
    
    async def search_emails(self, 
                          criteria: str = 'ALL',
                          mailbox: str = 'INBOX',
                          limit: Optional[int] = None) -> List[str]:
        """Search for emails matching criteria"""
        if not await self.select_mailbox(mailbox):
            return []
        
        try:
            response = await self.imap_client.search(criteria)
            if response.result != 'OK':
                return []
            
            email_ids = []
            for line in response.lines:
                ids = line.decode().split()
                email_ids.extend(ids)
            
            # Apply limit if specified
            if limit and len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent emails
            
            return email_ids
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    async def fetch_email(self, email_id: str, parts: str = '(RFC822)') -> Optional[Dict[str, Any]]:
        """Fetch email by ID"""
        if not await self._ensure_connection():
            return None
        
        try:
            response = await self.imap_client.fetch(email_id, parts)
            if response.result != 'OK' or not response.lines:
                return None
            
            # Parse email message
            email_data = b''.join(response.lines[0])
            message = email.message_from_bytes(email_data)
            
            return await self._parse_email_message(message, email_id)
            
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None
    
    async def _parse_email_message(self, message, email_id: str) -> Dict[str, Any]:
        """Parse email message into structured data"""
        try:
            # Extract headers
            subject = self._decode_header(message.get('Subject', ''))
            sender = self._decode_header(message.get('From', ''))
            recipient = self._decode_header(message.get('To', ''))
            date_str = message.get('Date', '')
            
            # Parse date
            try:
                email_date = email.utils.parsedate_to_datetime(date_str)
            except:
                email_date = datetime.utcnow()
            
            # Extract body
            body = await self._extract_email_body(message)
            
            # Extract domain from sender
            domain = self._extract_domain(sender)
            
            return {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'recipient': recipient,
                'domain': domain,
                'body': body,
                'date': email_date,
                'raw_message': str(message)
            }
            
        except Exception as e:
            logger.error(f"Error parsing email message: {e}")
            return {}
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ''
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string.strip()
            
        except Exception as e:
            logger.error(f"Error decoding header: {e}")
            return header
    
    async def _extract_email_body(self, message) -> str:
        """Extract email body content"""
        body = ""
        
        try:
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    elif content_type == "text/html" and not body:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # Convert HTML to plain text (basic)
                        body = re.sub(r'<[^>]+>', '', html_body)
            else:
                charset = message.get_content_charset() or 'utf-8'
                body = message.get_payload(decode=True).decode(charset, errors='ignore')
            
            return body.strip()
            
        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
            return ""
    
    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        try:
            # Remove display name if present
            if '<' in email_address and '>' in email_address:
                email_address = email_address.split('<')[1].split('>')[0]
            
            return email_address.split('@')[-1].lower()
        except:
            return ""
    
    async def get_recent_emails(self, 
                              hours: int = 24,
                              mailbox: str = 'INBOX',
                              limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent emails from specified timeframe"""
        if not await self.select_mailbox(mailbox):
            return []
        
        try:
            # Calculate date for search
            since_date = datetime.utcnow() - timedelta(hours=hours)
            date_str = since_date.strftime('%d-%b-%Y')
            
            # Search for emails since date
            criteria = f'SINCE {date_str}'
            email_ids = await self.search_emails(criteria, mailbox, limit)
            
            # Fetch email details
            emails = []
            for email_id in email_ids:
                email_data = await self.fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            # Sort by date (newest first)
            emails.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return []
    
    async def get_unread_emails(self, mailbox: str = 'INBOX') -> List[Dict[str, Any]]:
        """Get unread emails"""
        if not await self.select_mailbox(mailbox):
            return []
        
        try:
            email_ids = await self.search_emails('UNSEEN', mailbox)
            
            emails = []
            for email_id in email_ids:
                email_data = await self.fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting unread emails: {e}")
            return []
    
    async def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read"""
        if not await self._ensure_connection():
            return False
        
        try:
            response = await self.imap_client.store(email_id, '+FLAGS', '\\Seen')
            return response.result == 'OK'
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    async def get_email_count(self, mailbox: str = 'INBOX') -> Dict[str, int]:
        """Get email count statistics"""
        if not await self.select_mailbox(mailbox):
            return {}
        
        try:
            # Get total count
            total_ids = await self.search_emails('ALL', mailbox)
            total = len(total_ids)
            
            # Get unread count
            unread_ids = await self.search_emails('UNSEEN', mailbox)
            unread = len(unread_ids)
            
            # Get recent count (last 24 hours)
            recent_ids = await self.search_emails('RECENT', mailbox)
            recent = len(recent_ids)
            
            return {
                'total': total,
                'unread': unread,
                'recent': recent,
                'read': total - unread
            }
            
        except Exception as e:
            logger.error(f"Error getting email count: {e}")
            return {}
    
    async def search_by_sender(self, sender: str, mailbox: str = 'INBOX') -> List[Dict[str, Any]]:
        """Search emails by sender"""
        if not await self.select_mailbox(mailbox):
            return []
        
        try:
            criteria = f'FROM "{sender}"'
            email_ids = await self.search_emails(criteria, mailbox)
            
            emails = []
            for email_id in email_ids:
                email_data = await self.fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error searching emails by sender: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of email service"""
        try:
            # Test connection
            connection_ok = await self._ensure_connection()
            
            if not connection_ok:
                return {
                    'status': 'unhealthy',
                    'connection': False,
                    'error': 'Cannot establish IMAP connection'
                }
            
            # Test basic operations
            mailboxes = await self.get_mailboxes()
            inbox_selected = await self.select_mailbox('INBOX')
            
            return {
                'status': 'healthy',
                'connection': True,
                'mailboxes_count': len(mailboxes),
                'inbox_accessible': inbox_selected,
                'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None
            }
            
        except Exception as e:
            logger.error(f"Error in email service health check: {e}")
            return {
                'status': 'unhealthy',
                'connection': False,
                'error': str(e)
            }

# Create email service instance
email_service = EmailService()
