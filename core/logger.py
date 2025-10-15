"""
Logging configuration for Email Automation API
"""

import logging
import logging.handlers
from typing import Optional
import sys
from pathlib import Path

from .config import settings

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """Setup logging configuration"""
    
    # Use settings if parameters not provided
    level = level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    format_string = format_string or settings.LOG_FORMAT
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info("Logging configuration completed")

class EmailAutomationLogger:
    """Custom logger for email automation"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_email_received(self, sender: str, subject: str, email_id: str = None):
        """Log email received"""
        self.logger.info(f"EMAIL_RECEIVED: {sender} - {subject} - ID: {email_id}")
    
    def log_email_sent(self, recipient: str, subject: str, provider: str = "unknown"):
        """Log email sent"""
        self.logger.info(f"EMAIL_SENT: {recipient} - {subject} - Provider: {provider}")
    
    def log_email_replied(self, recipient: str, subject: str, reply_type: str = "auto"):
        """Log email replied"""
        self.logger.info(f"EMAIL_REPLIED: {recipient} - {subject} - Type: {reply_type}")
    
    def log_email_failed(self, recipient: str, subject: str, error: str):
        """Log email failed"""
        self.logger.error(f"EMAIL_FAILED: {recipient} - {subject} - Error: {error}")
    
    def log_domain_check(self, domain: str, allowed: bool):
        """Log domain check"""
        status = "ALLOWED" if allowed else "BLOCKED"
        self.logger.info(f"DOMAIN_CHECK: {domain} - {status}")
    
    def log_monitoring_start(self, service: str):
        """Log monitoring started"""
        self.logger.info(f"MONITORING_START: {service}")
    
    def log_monitoring_stop(self, service: str):
        """Log monitoring stopped"""
        self.logger.info(f"MONITORING_STOP: {service}")
    
    def log_health_check(self, service: str, status: str, details: str = ""):
        """Log health check"""
        self.logger.info(f"HEALTH_CHECK: {service} - {status} - {details}")
    
    def log_bulk_email_start(self, job_id: str, recipient_count: int):
        """Log bulk email job started"""
        self.logger.info(f"BULK_EMAIL_START: {job_id} - Recipients: {recipient_count}")
    
    def log_bulk_email_progress(self, job_id: str, sent: int, total: int):
        """Log bulk email progress"""
        percentage = (sent / total) * 100 if total > 0 else 0
        self.logger.info(f"BULK_EMAIL_PROGRESS: {job_id} - {sent}/{total} ({percentage:.1f}%)")
    
    def log_bulk_email_complete(self, job_id: str, sent: int, failed: int):
        """Log bulk email job completed"""
        self.logger.info(f"BULK_EMAIL_COMPLETE: {job_id} - Sent: {sent}, Failed: {failed}")
    
    def log_api_request(self, method: str, path: str, status_code: int, duration: float):
        """Log API request"""
        self.logger.info(f"API_REQUEST: {method} {path} - {status_code} - {duration:.3f}s")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        self.logger.error(f"ERROR: {context} - {str(error)}", exc_info=True)

# Create default logger instance
email_logger = EmailAutomationLogger("email_automation")
