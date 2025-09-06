"""
Health monitoring routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime

from ..models import StandardResponse, HealthStatus, ServiceHealth
from services import email_service, ai_service, sendgrid_service, email_monitor_service
from core.security import verify_api_key_optional
from core.database import database_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=HealthStatus)
async def get_health_status(
    auth_data: dict = Depends(verify_api_key_optional)
):
    """
    Get overall system health status
    
    Returns the health status of all system components.
    """
    try:
        # Get health status from all services
        email_health = await email_service.health_check()
        ai_health = await ai_service.health_check()
        sendgrid_health = await sendgrid_service.health_check()
        monitor_health = await email_monitor_service.health_check()
        
        # Check database health
        try:
            # Simple database health check
            async with database_manager.get_session() as session:
                await session.execute("SELECT 1")
            db_health = ServiceHealth(status="healthy", details={"connection": True})
        except Exception as e:
            db_health = ServiceHealth(status="unhealthy", details={"error": str(e)})
        
        # Determine overall status
        services = {
            "email": ServiceHealth(
                status=email_health.get("status", "unknown"),
                details=email_health
            ),
            "ai": ServiceHealth(
                status=ai_health.get("status", "unknown"),
                details=ai_health
            ),
            "sendgrid": ServiceHealth(
                status=sendgrid_health.get("status", "unknown"),
                details=sendgrid_health
            ),
            "monitor": ServiceHealth(
                status=monitor_health.get("status", "unknown"),
                details=monitor_health
            ),
            "database": db_health
        }
        
        # Overall status is healthy only if all services are healthy
        overall_status = "healthy" if all(
            service.status == "healthy" for service in services.values()
        ) else "unhealthy"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=services
        )
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            services={
                "error": ServiceHealth(status="error", details={"message": str(e)})
            }
        )

@router.get("/detailed", response_model=StandardResponse)
async def get_detailed_health(
    auth_data: dict = Depends(verify_api_key_optional)
):
    """
    Get detailed health information
    
    Returns comprehensive health information including performance metrics.
    """
    try:
        # Collect detailed health information
        health_data = {}
        
        # Email service details
        try:
            email_health = await email_service.health_check()
            email_counts = await email_service.get_email_count()
            health_data["email_service"] = {
                **email_health,
                "email_counts": email_counts
            }
        except Exception as e:
            health_data["email_service"] = {"status": "error", "error": str(e)}
        
        # AI service details
        try:
            ai_health = await ai_service.health_check()
            health_data["ai_service"] = ai_health
        except Exception as e:
            health_data["ai_service"] = {"status": "error", "error": str(e)}
        
        # SendGrid service details
        try:
            sendgrid_health = await sendgrid_service.health_check()
            health_data["sendgrid_service"] = sendgrid_health
        except Exception as e:
            health_data["sendgrid_service"] = {"status": "error", "error": str(e)}
        
        # Monitor service details
        try:
            monitor_status = await email_monitor_service.get_status()
            health_data["monitor_service"] = monitor_status
        except Exception as e:
            health_data["monitor_service"] = {"status": "error", "error": str(e)}
        
        # Database details
        try:
            async with database_manager.get_session() as session:
                # Get some basic database stats
                health_data["database"] = {
                    "status": "healthy",
                    "connection": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            health_data["database"] = {"status": "error", "error": str(e)}
        
        return StandardResponse(
            success=True,
            message="Detailed health information retrieved",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Error getting detailed health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic health checks
    
    Returns a simple response to verify the API is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Email Automation API"
    }

@router.get("/readiness", response_model=StandardResponse)
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns 200 if the service is ready to serve traffic.
    """
    try:
        # Check critical services
        critical_checks = []
        
        # Check database connectivity
        try:
            async with database_manager.get_session() as session:
                await session.execute("SELECT 1")
            critical_checks.append({"service": "database", "status": "ready"})
        except Exception as e:
            critical_checks.append({"service": "database", "status": "not_ready", "error": str(e)})
        
        # Check if any critical service is not ready
        not_ready = [check for check in critical_checks if check["status"] == "not_ready"]
        
        if not_ready:
            return StandardResponse(
                success=False,
                message="Service not ready",
                data={"checks": critical_checks, "not_ready": not_ready}
            )
        
        return StandardResponse(
            success=True,
            message="Service is ready",
            data={"checks": critical_checks}
        )
        
    except Exception as e:
        logger.error(f"Error in readiness check: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns 200 if the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics", response_model=StandardResponse)
async def get_metrics(
    auth_data: dict = Depends(verify_api_key_optional)
):
    """
    Get system metrics
    
    Returns performance and usage metrics.
    """
    try:
        # Collect various metrics
        metrics = {}
        
        # Email processing metrics
        try:
            monitor_status = await email_monitor_service.get_status()
            metrics["email_processing"] = {
                "is_running": monitor_status.get("is_running", False),
                "processed_emails": monitor_status.get("processed_emails_count", 0),
                "last_check": monitor_status.get("last_check"),
                "stats": monitor_status.get("stats", {})
            }
        except Exception as e:
            metrics["email_processing"] = {"error": str(e)}
        
        # Database metrics (basic)
        try:
            # Get some basic database metrics
            from datetime import timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            
            recent_logs = await database_manager.get_email_logs(
                limit=1000,
                start_date=start_date,
                end_date=end_date
            )
            
            metrics["database"] = {
                "recent_logs_count": len(recent_logs),
                "period": "24_hours"
            }
        except Exception as e:
            metrics["database"] = {"error": str(e)}
        
        # Service availability metrics
        health_status = await get_health_status()
        service_availability = {}
        for service_name, service_health in health_status.services.items():
            service_availability[service_name] = service_health.status == "healthy"
        
        metrics["service_availability"] = service_availability
        
        return StandardResponse(
            success=True,
            message="System metrics retrieved",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-services", response_model=StandardResponse)
async def test_all_services(
    auth_data: dict = Depends(verify_api_key_optional)
):
    """
    Test all services connectivity
    
    Performs comprehensive testing of all service connections.
    """
    try:
        test_results = {}
        
        # Test email service
        try:
            email_health = await email_service.health_check()
            test_results["email_service"] = {
                "status": "pass" if email_health.get("status") == "healthy" else "fail",
                "details": email_health
            }
        except Exception as e:
            test_results["email_service"] = {"status": "fail", "error": str(e)}
        
        # Test AI service
        try:
            ai_health = await ai_service.health_check()
            test_results["ai_service"] = {
                "status": "pass" if ai_health.get("status") == "healthy" else "fail",
                "details": ai_health
            }
        except Exception as e:
            test_results["ai_service"] = {"status": "fail", "error": str(e)}
        
        # Test SendGrid service
        try:
            sendgrid_health = await sendgrid_service.health_check()
            test_results["sendgrid_service"] = {
                "status": "pass" if sendgrid_health.get("status") == "healthy" else "fail",
                "details": sendgrid_health
            }
        except Exception as e:
            test_results["sendgrid_service"] = {"status": "fail", "error": str(e)}
        
        # Test database
        try:
            async with database_manager.get_session() as session:
                await session.execute("SELECT 1")
            test_results["database"] = {"status": "pass", "connection": True}
        except Exception as e:
            test_results["database"] = {"status": "fail", "error": str(e)}
        
        # Overall test result
        all_passed = all(result.get("status") == "pass" for result in test_results.values())
        
        return StandardResponse(
            success=all_passed,
            message="Service tests completed" if all_passed else "Some service tests failed",
            data=test_results
        )
        
    except Exception as e:
        logger.error(f"Error testing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))
