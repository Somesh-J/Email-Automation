"""
FastAPI Email Automation Application
====================================

A modern, scalable email automation service built with FastAPI.
This application provides comprehensive email management features including:
- Email monitoring and processing
- AI-powered auto-replies
- Bulk email sending
- Domain management
- Health monitoring
- Real-time notifications

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Author: Somesh Jyothula
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# Import route modules
from api.routes import (
    email_processing,
    domain_management,
    monitoring,
    health,
    bulk_email,
    analytics,
    settings,
    # templates  # Temporarily disabled - needs MongoDB migration
)

# Import core services
from core.database import database_manager
from core.config import settings as app_settings
from core.logger import setup_logging
from services.email_monitor import EmailMonitorService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
email_monitor_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Email Automation FastAPI Application...")
    
    # Initialize database
    if app_settings.USE_MONGODB:
        await database_manager.connect()
    else:
        await database_manager.create_tables()
        await database_manager.init_default_data()
    
    # Initialize email monitor service
    global email_monitor_service
    email_monitor_service = EmailMonitorService()
    
    # Start background services if enabled
    if hasattr(app_settings, 'AUTO_START_MONITORING') and app_settings.AUTO_START_MONITORING:
        await email_monitor_service.start()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Email Automation Application...")
    
    # Stop background services
    if email_monitor_service:
        await email_monitor_service.stop()
    
    # Close database connections
    await database_manager.close()
    
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Email Automation API",
    description="""
    ## Email Automation Service
    
    A comprehensive email automation platform providing:
    
    * **Email Processing**: Automated email monitoring and processing
    * **AI Replies**: Smart auto-replies powered by AI
    * **Bulk Email**: Scalable bulk email sending with rate limiting
    * **Domain Management**: Whitelist/blacklist domain management
    * **Health Monitoring**: Real-time system health monitoring
    * **Analytics**: Detailed email analytics and reporting
    
    ### Authentication
    
    This API uses API key authentication. Include your API key in the header:
    ```
    X-API-Key: your-api-key-here
    ```
    
    ### Rate Limiting
    
    API calls are rate limited to prevent abuse. See individual endpoints for specific limits.
    """,
    version="1.0.0",
    terms_of_service="https://zetaleap.ai/terms",
    contact={
        "name": "ZetaLeap Support",
        "url": "https://zetaleap.ai/contact",
        "email": "support@zetaleap.ai",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(
    email_processing.router,
    prefix="/api/v1/email",
    tags=["Email Processing"]
)

app.include_router(
    domain_management.router,
    prefix="/api/v1/domains",
    tags=["Domain Management"]
)

app.include_router(
    monitoring.router,
    prefix="/api/v1/monitor",
    tags=["Monitoring"]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

app.include_router(
    bulk_email.router,
    prefix="/api/v1/bulk",
    tags=["Bulk Email"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

app.include_router(
    settings.router,
    prefix="/api/v1/settings",
    tags=["Settings"]
)

# Temporarily disabled - needs MongoDB migration
# app.include_router(
#     templates.router,
#     prefix="/api/v1/templates",
#     tags=["Templates"]
# )

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Email Automation API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health/status"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": f"The requested resource {request.url.path} was not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=app_settings.DEBUG,
        log_level="info"
    )
