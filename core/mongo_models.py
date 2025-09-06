"""
MongoDB models using Beanie ODM for Email Automation API
"""

from beanie import Document, Indexed
from pymongo import IndexModel, ASCENDING, DESCENDING
from pydantic import Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class EmailStatus(str, Enum):
    """Email status enumeration"""
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    FLAGGED = "flagged"
    ARCHIVED = "archived"

class BulkJobStatus(str, Enum):
    """Bulk job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EmailMongo(Document):
    """Email document for MongoDB"""
    
    email_id: str = Field(..., description="Unique email identifier")
    subject: str = Field(..., description="Email subject")
    sender: EmailStr = Field(..., description="Sender email address")
    recipients: List[EmailStr] = Field(default=[], description="Email recipients")
    cc: List[EmailStr] = Field(default=[], description="CC recipients")
    bcc: List[EmailStr] = Field(default=[], description="BCC recipients")
    body: str = Field(default="", description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML email body")
    attachments: List[str] = Field(default=[], description="Attachment file paths")
    headers: Dict[str, Any] = Field(default={}, description="Email headers")
    status: EmailStatus = Field(default=EmailStatus.UNREAD, description="Email status")
    thread_id: Optional[str] = Field(None, description="Email thread identifier")
    in_reply_to: Optional[str] = Field(None, description="Reply to email ID")
    date_received: datetime = Field(default_factory=datetime.utcnow, description="Date received")
    date_read: Optional[datetime] = Field(None, description="Date marked as read")
    date_replied: Optional[datetime] = Field(None, description="Date replied")
    ai_reply_generated: bool = Field(default=False, description="Whether AI reply was generated")
    ai_reply_sent: bool = Field(default=False, description="Whether AI reply was sent")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")
    sentiment_label: Optional[str] = Field(None, description="Sentiment analysis label")
    domain: str = Field(..., description="Sender domain")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "emails"
        indexes = [
            IndexModel([("email_id", ASCENDING)], unique=True),
            IndexModel([("sender", ASCENDING)]),
            IndexModel([("domain", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("date_received", DESCENDING)]),
            IndexModel([("thread_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

class DomainMongo(Document):
    """Domain document for MongoDB"""
    
    domain: str = Field(..., description="Domain name")
    is_allowed: bool = Field(default=True, description="Whether domain is allowed")
    is_blocked: bool = Field(default=False, description="Whether domain is blocked")
    auto_reply_enabled: bool = Field(default=True, description="Enable auto-reply for this domain")
    reply_template_id: Optional[str] = Field(None, description="Default reply template ID")
    max_emails_per_day: Optional[int] = Field(None, description="Max emails allowed per day")
    description: Optional[str] = Field(None, description="Domain description")
    tags: List[str] = Field(default=[], description="Domain tags")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "domains"
        indexes = [
            IndexModel([("domain", ASCENDING)], unique=True),
            IndexModel([("is_allowed", ASCENDING)]),
            IndexModel([("is_blocked", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

class EmailTemplateMongo(Document):
    """Email template document for MongoDB"""
    
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject template")
    body: str = Field(..., description="Email body template")
    html_body: Optional[str] = Field(None, description="HTML email body template")
    category: Optional[str] = Field(None, description="Template category")
    variables: List[str] = Field(default=[], description="Template variable names")
    is_active: bool = Field(default=True, description="Whether template is active")
    usage_count: int = Field(default=0, description="Number of times template was used")
    tags: List[str] = Field(default=[], description="Template tags")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "email_templates"
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
            IndexModel([("category", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

class BulkEmailJobMongo(Document):
    """Bulk email job document for MongoDB"""
    
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Job identifier")
    name: str = Field(..., description="Job name")
    template_id: Optional[str] = Field(None, description="Email template ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    html_body: Optional[str] = Field(None, description="HTML email body")
    recipients: List[EmailStr] = Field(..., description="Email recipients")
    variables: Dict[str, Any] = Field(default={}, description="Template variables")
    status: BulkJobStatus = Field(default=BulkJobStatus.PENDING, description="Job status")
    total_emails: int = Field(default=0, description="Total emails to send")
    sent_count: int = Field(default=0, description="Number of emails sent")
    failed_count: int = Field(default=0, description="Number of failed emails")
    error_messages: List[str] = Field(default=[], description="Error messages")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "bulk_email_jobs"
        indexes = [
            IndexModel([("job_id", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("scheduled_at", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

class MonitoringStatusMongo(Document):
    """Monitoring status document for MongoDB"""
    
    service_name: str = Field(..., description="Service name")
    is_active: bool = Field(default=False, description="Whether monitoring is active")
    last_check: Optional[datetime] = Field(None, description="Last check timestamp")
    next_check: Optional[datetime] = Field(None, description="Next scheduled check")
    check_interval: int = Field(default=30, description="Check interval in seconds")
    error_count: int = Field(default=0, description="Number of consecutive errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    health_status: str = Field(default="unknown", description="Health status")
    metrics: Dict[str, Any] = Field(default={}, description="Service metrics")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "monitoring_status"
        indexes = [
            IndexModel([("service_name", ASCENDING)], unique=True),
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("last_check", DESCENDING)]),
            IndexModel([("health_status", ASCENDING)])
        ]

class APIKeyMongo(Document):
    """API key document for MongoDB"""
    
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Key identifier")
    key_hash: str = Field(..., description="Hashed API key")
    name: str = Field(..., description="Key name/description")
    permissions: List[str] = Field(default=[], description="Key permissions")
    is_active: bool = Field(default=True, description="Whether key is active")
    usage_count: int = Field(default=0, description="Number of times key was used")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    expires_at: Optional[datetime] = Field(None, description="Key expiration time")
    rate_limit: Optional[int] = Field(None, description="Custom rate limit for this key")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "api_keys"
        indexes = [
            IndexModel([("key_id", ASCENDING)], unique=True),
            IndexModel([("key_hash", ASCENDING)], unique=True),
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

class SystemSettingsMongo(Document):
    """System settings document for MongoDB"""
    
    setting_key: str = Field(..., description="Setting key")
    setting_value: Any = Field(..., description="Setting value")
    data_type: str = Field(..., description="Data type (str, int, bool, float, list, dict)")
    description: Optional[str] = Field(None, description="Setting description")
    category: Optional[str] = Field(None, description="Setting category")
    is_encrypted: bool = Field(default=False, description="Whether value is encrypted")
    is_system: bool = Field(default=False, description="Whether this is a system setting")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Settings:
        name = "system_settings"
        indexes = [
            IndexModel([("setting_key", ASCENDING)], unique=True),
            IndexModel([("category", ASCENDING)]),
            IndexModel([("is_system", ASCENDING)])
        ]

class EmailLogMongo(Document):
    """Email log document for MongoDB"""
    
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Log identifier")
    email_id: Optional[str] = Field(None, description="Related email ID")
    action: str = Field(..., description="Action performed")
    status: str = Field(..., description="Action status")
    details: Dict[str, Any] = Field(default={}, description="Action details")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    user_id: Optional[str] = Field(None, description="User who performed action")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    class Settings:
        name = "email_logs"
        indexes = [
            IndexModel([("log_id", ASCENDING)], unique=True),
            IndexModel([("email_id", ASCENDING)]),
            IndexModel([("action", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]

# List of all MongoDB document classes for easy initialization
MONGO_DOCUMENTS = [
    EmailMongo,
    DomainMongo,
    EmailTemplateMongo,
    BulkEmailJobMongo,
    MonitoringStatusMongo,
    APIKeyMongo,
    SystemSettingsMongo,
    EmailLogMongo
]
