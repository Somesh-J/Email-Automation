"""
Settings routes
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from ..models import StandardResponse, SystemSettings
from core.security import verify_api_key, require_permissions
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=StandardResponse)
async def get_settings(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get current system settings
    
    Retrieve all configurable system settings.
    """
    try:
        current_settings = SystemSettings(
            email_check_interval=settings.EMAIL_CHECK_INTERVAL,
            enable_auto_reply=settings.ENABLE_AUTO_REPLY,
            max_emails_per_check=settings.MAX_EMAILS_PER_CHECK,
            bulk_email_batch_size=settings.BULK_EMAIL_BATCH_SIZE,
            bulk_email_delay=settings.BULK_EMAIL_DELAY,
            rate_limit_requests=settings.RATE_LIMIT_REQUESTS,
            rate_limit_period=settings.RATE_LIMIT_PERIOD
        )
        
        return StandardResponse(
            success=True,
            message="System settings retrieved successfully",
            data=current_settings.dict()
        )
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/", response_model=StandardResponse)
async def update_settings(
    new_settings: SystemSettings,
    auth_data: dict = Depends(require_permissions(["settings_manage"]))
):
    """
    Update system settings
    
    Update configurable system settings.
    """
    try:
        # In a real implementation, these would be stored in database
        # For now, we'll return success but note that changes are temporary
        
        return StandardResponse(
            success=True,
            message="Settings updated successfully (Note: Changes are temporary in this demo)",
            data={
                "updated_settings": new_settings.dict(),
                "note": "In production, settings would be persisted to database"
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email", response_model=StandardResponse)
async def get_email_settings(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get email-specific settings
    
    Retrieve email configuration settings.
    """
    try:
        email_settings = {
            "imap_server": settings.IMAP_SERVER,
            "imap_port": settings.IMAP_PORT,
            "imap_use_ssl": settings.IMAP_USE_SSL,
            "from_email": settings.FROM_EMAIL,
            "from_name": settings.FROM_NAME,
            "check_interval": settings.EMAIL_CHECK_INTERVAL,
            "max_emails_per_check": settings.MAX_EMAILS_PER_CHECK,
            "enable_auto_reply": settings.ENABLE_AUTO_REPLY
        }
        
        return StandardResponse(
            success=True,
            message="Email settings retrieved successfully",
            data=email_settings
        )
        
    except Exception as e:
        logger.error(f"Error getting email settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/email", response_model=StandardResponse)
async def update_email_settings(
    email_check_interval: int = None,
    enable_auto_reply: bool = None,
    max_emails_per_check: int = None,
    auth_data: dict = Depends(require_permissions(["settings_manage"]))
):
    """
    Update email-specific settings
    
    Update email configuration settings.
    """
    try:
        updates = {}
        
        if email_check_interval is not None:
            if email_check_interval < 10:
                raise HTTPException(status_code=400, detail="Check interval must be at least 10 seconds")
            updates["email_check_interval"] = email_check_interval
        
        if enable_auto_reply is not None:
            updates["enable_auto_reply"] = enable_auto_reply
        
        if max_emails_per_check is not None:
            if max_emails_per_check < 1 or max_emails_per_check > 1000:
                raise HTTPException(status_code=400, detail="Max emails per check must be between 1 and 1000")
            updates["max_emails_per_check"] = max_emails_per_check
        
        return StandardResponse(
            success=True,
            message="Email settings updated successfully",
            data={
                "updated_settings": updates,
                "note": "Settings updates are temporary in this demo"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai", response_model=StandardResponse)
async def get_ai_settings(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get AI-specific settings
    
    Retrieve AI configuration settings.
    """
    try:
        ai_settings = {
            "ai_provider": settings.AI_PROVIDER,
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "openai_configured": bool(settings.OPENAI_API_KEY)
        }
        
        return StandardResponse(
            success=True,
            message="AI settings retrieved successfully",
            data=ai_settings
        )
        
    except Exception as e:
        logger.error(f"Error getting AI settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/ai", response_model=StandardResponse)
async def update_ai_settings(
    ai_provider: str = None,
    auth_data: dict = Depends(require_permissions(["settings_manage"]))
):
    """
    Update AI-specific settings
    
    Update AI configuration settings.
    """
    try:
        updates = {}
        
        if ai_provider is not None:
            if ai_provider not in ["gemini", "openai"]:
                raise HTTPException(status_code=400, detail="AI provider must be 'gemini' or 'openai'")
            updates["ai_provider"] = ai_provider
        
        return StandardResponse(
            success=True,
            message="AI settings updated successfully",
            data={
                "updated_settings": updates,
                "note": "Settings updates are temporary in this demo"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security", response_model=StandardResponse)
async def get_security_settings(
    auth_data: dict = Depends(require_permissions(["security_view"]))
):
    """
    Get security settings
    
    Retrieve security configuration settings.
    """
    try:
        security_settings = {
            "rate_limit_requests": settings.RATE_LIMIT_REQUESTS,
            "rate_limit_period": settings.RATE_LIMIT_PERIOD,
            "api_key_count": len(settings.VALID_API_KEYS),
            "allowed_origins": settings.ALLOWED_ORIGINS
        }
        
        return StandardResponse(
            success=True,
            message="Security settings retrieved successfully",
            data=security_settings
        )
        
    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/security", response_model=StandardResponse)
async def update_security_settings(
    rate_limit_requests: int = None,
    rate_limit_period: int = None,
    auth_data: dict = Depends(require_permissions(["security_manage"]))
):
    """
    Update security settings
    
    Update security configuration settings.
    """
    try:
        updates = {}
        
        if rate_limit_requests is not None:
            if rate_limit_requests < 1 or rate_limit_requests > 10000:
                raise HTTPException(status_code=400, detail="Rate limit requests must be between 1 and 10000")
            updates["rate_limit_requests"] = rate_limit_requests
        
        if rate_limit_period is not None:
            if rate_limit_period < 60 or rate_limit_period > 86400:  # 1 minute to 24 hours
                raise HTTPException(status_code=400, detail="Rate limit period must be between 60 and 86400 seconds")
            updates["rate_limit_period"] = rate_limit_period
        
        return StandardResponse(
            success=True,
            message="Security settings updated successfully",
            data={
                "updated_settings": updates,
                "note": "Settings updates are temporary in this demo"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/defaults", response_model=StandardResponse)
async def get_default_settings(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get default settings
    
    Retrieve default configuration values.
    """
    try:
        defaults = {
            "email_check_interval": 30,
            "enable_auto_reply": True,
            "max_emails_per_check": 50,
            "bulk_email_batch_size": 10,
            "bulk_email_delay": 1.0,
            "rate_limit_requests": 100,
            "rate_limit_period": 3600,
            "ai_provider": "gemini"
        }
        
        return StandardResponse(
            success=True,
            message="Default settings retrieved successfully",
            data=defaults
        )
        
    except Exception as e:
        logger.error(f"Error getting default settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset", response_model=StandardResponse)
async def reset_to_defaults(
    auth_data: dict = Depends(require_permissions(["settings_manage"]))
):
    """
    Reset settings to defaults
    
    Reset all settings to their default values.
    """
    try:
        # In a real implementation, this would reset settings in database
        
        return StandardResponse(
            success=True,
            message="Settings reset to defaults successfully",
            data={
                "note": "In production, settings would be reset in database",
                "action": "reset_to_defaults"
            }
        )
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
