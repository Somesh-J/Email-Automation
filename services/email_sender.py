"""
Unified email sender service that supports multiple email providers
Automatically switches between SendGrid and Resend based on configuration
"""

import logging
from typing import List, Dict, Any, Optional

from core.config import settings
from services.sendgrid_service import sendgrid_service
from services.resend_service import resend_service

logger = logging.getLogger(__name__)


class EmailSenderService:
    """
    Unified email sender service
    Supports both SendGrid and Resend email providers
    """
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER.lower()
        self._verify_configuration()
    
    def _verify_configuration(self):
        """Verify email provider configuration"""
        if self.provider == "sendgrid":
            if not settings.SENDGRID_API_KEY:
                logger.warning("SendGrid selected but API key not configured")
            else:
                logger.info("Email sender initialized with SendGrid")
        elif self.provider == "resend":
            if not settings.RESEND_API_KEY:
                logger.warning("Resend selected but API key not configured")
            else:
                logger.info("Email sender initialized with Resend")
        else:
            logger.error(f"Unknown email provider: {self.provider}")
            logger.info("Defaulting to SendGrid")
            self.provider = "sendgrid"
    
    def get_active_service(self):
        """Get the active email service based on provider"""
        if self.provider == "resend":
            return resend_service
        else:
            return sendgrid_service
    
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
        Send single email using configured provider
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            content_type: Content type (text/plain or text/html)
            reply_to: Reply-to email address
            attachments: List of attachments (optional)
            
        Returns:
            Dict with success status and details
        """
        
        service = self.get_active_service()
        
        try:
            logger.info(f"Sending email to {to_email} via {self.provider.upper()}")
            
            result = await service.send_email(
                to_email=to_email,
                subject=subject,
                content=content,
                from_email=from_email,
                from_name=from_name,
                content_type=content_type,
                reply_to=reply_to
            )
            
            # Add provider info to result
            result["provider"] = self.provider
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending email via {self.provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider
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
        Send bulk emails using configured provider
        
        Args:
            recipients: List of recipient dictionaries
            subject: Email subject
            content: Email content
            from_email: Sender email
            from_name: Sender name
            content_type: Content type
            batch_size: Batch size for sending
            delay: Delay between batches
            
        Returns:
            Dict with statistics
        """
        
        service = self.get_active_service()
        
        try:
            logger.info(f"Sending bulk email to {len(recipients)} recipients via {self.provider.upper()}")
            
            result = await service.send_bulk_emails(
                recipients=recipients,
                subject=subject,
                content=content,
                from_email=from_email,
                from_name=from_name,
                content_type=content_type,
                batch_size=batch_size,
                delay=delay
            )
            
            # Add provider info to result
            result["provider"] = self.provider
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending bulk emails via {self.provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider
            }
    
    async def send_html_email(self,
                            to_email: str,
                            subject: str,
                            html_content: str,
                            text_content: Optional[str] = None,
                            from_email: Optional[str] = None,
                            from_name: Optional[str] = None,
                            reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Send HTML email with optional text fallback
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text fallback (optional)
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to address
            
        Returns:
            Dict with result
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            content=html_content,
            from_email=from_email,
            from_name=from_name,
            content_type="text/html",
            reply_to=reply_to
        )
    
    async def send_template_email(self,
                                 to_email: str,
                                 template_name: str,
                                 template_data: Dict[str, Any],
                                 from_email: Optional[str] = None,
                                 from_name: Optional[str] = None,
                                 reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email using template (provider-specific implementation)
        
        Note: SendGrid and Resend handle templates differently
        """
        
        service = self.get_active_service()
        
        if hasattr(service, 'send_with_template'):
            return await service.send_with_template(
                to_email=to_email,
                template_id=template_name,
                template_data=template_data,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to
            )
        else:
            return {
                "success": False,
                "error": f"Template support not available for {self.provider}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check email service health
        
        Returns:
            Dict with health status
        """
        
        service = self.get_active_service()
        
        try:
            result = await service.health_check()
            result["configured_provider"] = self.provider
            return result
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "configured_provider": self.provider,
                "error": str(e)
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the active provider
        
        Returns:
            Dict with provider information
        """
        
        return {
            "provider": self.provider,
            "from_email": settings.FROM_EMAIL,
            "from_name": settings.FROM_NAME,
            "sendgrid_configured": bool(settings.SENDGRID_API_KEY),
            "resend_configured": bool(settings.RESEND_API_KEY)
        }


# Create global email sender service instance
email_sender_service = EmailSenderService()
