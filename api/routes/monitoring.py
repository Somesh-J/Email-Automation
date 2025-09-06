"""
Monitoring routes
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from ..models import StandardResponse, MonitoringStatus, MonitoringSettings
from services import email_monitor_service
from core.security import verify_api_key, require_permissions

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=MonitoringStatus)
async def get_monitoring_status(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get current monitoring status
    """
    try:
        status = await email_monitor_service.get_status()
        
        return MonitoringStatus(
            is_running=status.get('is_running', False),
            check_interval=status.get('check_interval', 30),
            last_check=status.get('last_check'),
            processed_emails_count=status.get('processed_emails_count', 0),
            allowed_domains_count=status.get('allowed_domains_count', 0),
            stats=status.get('stats', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start", response_model=StandardResponse)
async def start_monitoring(
    auth_data: dict = Depends(require_permissions(["monitor_control"]))
):
    """
    Start email monitoring
    """
    try:
        await email_monitor_service.start()
        
        return StandardResponse(
            success=True,
            message="Email monitoring started successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=StandardResponse)
async def stop_monitoring(
    auth_data: dict = Depends(require_permissions(["monitor_control"]))
):
    """
    Stop email monitoring
    """
    try:
        await email_monitor_service.stop()
        
        return StandardResponse(
            success=True,
            message="Email monitoring stopped successfully"
        )
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart", response_model=StandardResponse)
async def restart_monitoring(
    auth_data: dict = Depends(require_permissions(["monitor_control"]))
):
    """
    Restart email monitoring
    """
    try:
        await email_monitor_service.restart()
        
        return StandardResponse(
            success=True,
            message="Email monitoring restarted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error restarting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force-check", response_model=StandardResponse)
async def force_email_check(
    auth_data: dict = Depends(require_permissions(["monitor_control"]))
):
    """
    Force immediate email check
    """
    try:
        result = await email_monitor_service.force_check()
        
        return StandardResponse(
            success=result.get('success', False),
            message=result.get('message', 'Email check completed'),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error forcing email check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings", response_model=StandardResponse)
async def update_monitoring_settings(
    settings: MonitoringSettings,
    auth_data: dict = Depends(require_permissions(["monitor_control"]))
):
    """
    Update monitoring settings
    """
    try:
        await email_monitor_service.update_settings(
            check_interval=settings.check_interval,
            enable_auto_reply=settings.enable_auto_reply,
            max_emails_per_check=settings.max_emails_per_check
        )
        
        return StandardResponse(
            success=True,
            message="Monitoring settings updated successfully",
            data=settings.dict()
        )
        
    except Exception as e:
        logger.error(f"Error updating monitoring settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=StandardResponse)
async def get_monitoring_health(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get monitoring service health
    """
    try:
        health = await email_monitor_service.health_check()
        
        return StandardResponse(
            success=health.get('status') == 'healthy',
            message="Monitoring health check completed",
            data=health
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
