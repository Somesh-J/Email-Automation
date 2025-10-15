"""
Resend service for sending emails
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
import httpx
from datetime import datetime

from core.config import settings
from core.logger import email_logger

logger = logging.getLogger(__name__)

class ResendService:
    """Service for sending emails via Resend API"""
    
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.api_url = "https://api.resend.com"
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        self._verify_configuration()
    
    def _verify_configuration(self):
        """Verify Resend configuration"""
        if not self.api_key:
            logger.warning("Resend API key not configured")
        else:
            logger.info("Resend service initialized")
    
    async def send_email(self, 
                        to_email: str,
                        subject: str,
                        content: str,
                        from_email: Optional[str] = None,
                        from_name: Optional[str] = None,
                        content_type: str = "text/plain",
                        reply_to: Optional[str] = None,
                        attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send single email via Resend API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (text or HTML)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional, uses default)
            content_type: Content type (text/plain or text/html)
            reply_to: Reply-to email address
            attachments: List of attachments (optional)
            
        Returns:
            Dict with success status and message_id or error
        """
        
        if not self.api_key:
            return {
                "success": False,
                "error": "Resend API key not configured"
            }
        
        try:
            # Prepare sender
            from_email = from_email or self.from_email
            from_name = from_name or self.from_name
            
            if from_name:
                from_address = f"{from_name} <{from_email}>"
            else:
                from_address = from_email
            
            # Prepare email payload
            payload = {
                "from": from_address,
                "to": [to_email],
                "subject": subject
            }
            
            # Add content based on type
            if content_type == "text/html":
                payload["html"] = content
            else:
                payload["text"] = content
            
            # Add reply-to if provided
            if reply_to:
                payload["reply_to"] = reply_to
            
            # Add attachments if provided
            if attachments:
                payload["attachments"] = attachments
            
            # Send email via Resend API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    message_id = result.get("id")
                    
                    email_logger.log_email_sent(to_email, subject, "resend")
                    
                    return {
                        "success": True,
                        "message_id": message_id,
                        "status_code": response.status_code
                    }
                else:
                    error_detail = response.text
                    logger.error(f"Resend send failed: {response.status_code} - {error_detail}")
                    
                    return {
                        "success": False,
                        "error": f"Resend error: {response.status_code}",
                        "details": error_detail,
                        "status_code": response.status_code
                    }
                    
        except httpx.TimeoutException:
            logger.error("Resend API timeout")
            email_logger.log_email_failed(to_email, subject, "Timeout")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"Error sending email via Resend: {e}")
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
        """
        Send bulk emails via Resend API
        
        Args:
            recipients: List of recipient dictionaries with 'email' key
            subject: Email subject
            content: Email content
            from_email: Sender email
            from_name: Sender name
            content_type: Content type
            batch_size: Number of emails to send per batch
            delay: Delay between batches in seconds
            
        Returns:
            Dict with statistics (total, sent, failed)
        """
        
        if not self.api_key:
            return {
                "success": False,
                "error": "Resend API key not configured"
            }
        
        total = len(recipients)
        sent_count = 0
        failed_count = 0
        errors = []
        
        logger.info(f"Starting bulk email send to {total} recipients via Resend")
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = recipients[i:i + batch_size]
            
            # Send emails in batch concurrently
            tasks = []
            for recipient in batch:
                email = recipient.get("email")
                if not email:
                    continue
                
                # Personalize content if variables provided
                personalized_content = content
                if "variables" in recipient:
                    for key, value in recipient["variables"].items():
                        personalized_content = personalized_content.replace(
                            f"{{{key}}}", str(value)
                        )
                
                task = self.send_email(
                    to_email=email,
                    subject=subject,
                    content=personalized_content,
                    from_email=from_email,
                    from_name=from_name,
                    content_type=content_type
                )
                tasks.append(task)
            
            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and failures
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    sent_count += 1
                else:
                    failed_count += 1
                    if isinstance(result, dict):
                        errors.append(result.get("error", "Unknown error"))
                    else:
                        errors.append(str(result))
            
            # Delay between batches (except last batch)
            if i + batch_size < total:
                await asyncio.sleep(delay)
            
            # Log progress
            progress = min(i + batch_size, total)
            logger.info(f"Bulk email progress: {progress}/{total} ({sent_count} sent, {failed_count} failed)")
        
        logger.info(f"Bulk email completed: {sent_count} sent, {failed_count} failed")
        
        return {
            "success": True,
            "total": total,
            "sent": sent_count,
            "failed": failed_count,
            "errors": errors[:10]  # Return first 10 errors
        }
    
    async def send_with_template(self,
                                to_email: str,
                                template_id: str,
                                template_data: Dict[str, Any],
                                from_email: Optional[str] = None,
                                from_name: Optional[str] = None,
                                reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email using Resend template
        
        Note: Resend templates work differently than SendGrid
        This is a placeholder for template support
        """
        
        logger.warning("Resend template support not yet implemented")
        return {
            "success": False,
            "error": "Template support not implemented for Resend"
        }
    
    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify email address (if Resend supports it)
        
        Note: Check Resend documentation for email verification API
        """
        
        logger.warning("Email verification not implemented for Resend")
        return {
            "success": False,
            "error": "Email verification not implemented for Resend"
        }
    
    async def get_email_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get email delivery status from Resend
        
        Args:
            message_id: Message ID from send response
            
        Returns:
            Dict with email status information
        """
        
        if not self.api_key:
            return {
                "success": False,
                "error": "Resend API key not configured"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/emails/{message_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": data.get("last_event"),
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Status check failed: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting email status from Resend: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Resend service health
        
        Returns:
            Dict with health status
        """
        
        if not self.api_key:
            return {
                "status": "unhealthy",
                "service": "resend",
                "error": "API key not configured"
            }
        
        try:
            # Test API connection with a simple request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/domains",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    timeout=5.0
                )
                
                if response.status_code in [200, 401, 403]:  # 401/403 means API is accessible
                    return {
                        "status": "healthy",
                        "service": "resend",
                        "api_accessible": True,
                        "from_email": self.from_email
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "service": "resend",
                        "error": f"API returned status {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Resend health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "resend",
                "error": str(e)
            }


# Create global Resend service instance
resend_service = ResendService()
