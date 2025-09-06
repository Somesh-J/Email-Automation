"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class EmailAction(str, Enum):
    """Email action types"""
    RECEIVED = "received"
    REPLIED = "replied"
    AUTO_REPLIED = "auto_replied"
    FAILED = "failed"

class ReplyType(str, Enum):
    """Reply types"""
    AUTO = "auto"
    MANUAL = "manual"
    AI = "ai"

class EmailStatus(str, Enum):
    """Email status types"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class SentimentType(str, Enum):
    """Sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class UrgencyLevel(str, Enum):
    """Urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Email Models
class EmailBase(BaseModel):
    """Base email model"""
    sender: EmailStr
    subject: str
    body: str

class EmailInbound(EmailBase):
    """Inbound email model"""
    recipient: Optional[EmailStr] = None
    headers: Optional[Dict[str, str]] = {}
    timestamp: Optional[datetime] = None

class EmailReply(BaseModel):
    """Email reply model"""
    to_email: EmailStr
    subject: str
    content: str
    content_type: str = "text/plain"
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None

class EmailTemplate(BaseModel):
    """Email template model"""
    name: str
    subject: str
    content: str
    template_type: str = "auto_reply"
    variables: List[str] = []
    is_active: bool = True

# Bulk Email Models
class BulkEmailRecipient(BaseModel):
    """Bulk email recipient model"""
    email: EmailStr
    data: Optional[Dict[str, Any]] = {}

class BulkEmailRequest(BaseModel):
    """Bulk email request model"""
    recipients: List[Union[EmailStr, BulkEmailRecipient]]
    subject: str
    content: str
    content_type: str = "text/plain"
    from_name: Optional[str] = None
    batch_size: int = 10
    delay: float = 1.0
    
    @validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError("Recipients list cannot be empty")
        if len(v) > 1000:  # Adjust based on your needs
            raise ValueError("Too many recipients")
        return v
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Batch size must be between 1 and 100")
        return v

class BulkEmailJob(BaseModel):
    """Bulk email job model"""
    job_id: str
    name: Optional[str] = None
    status: str = "pending"
    recipients_count: int
    sent_count: int = 0
    failed_count: int = 0
    progress_percentage: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None

# Domain Models
class DomainBase(BaseModel):
    """Base domain model"""
    domain: str
    is_allowed: bool = True
    auto_reply_enabled: bool = True
    notes: Optional[str] = None

class DomainCreate(DomainBase):
    """Domain creation model"""
    pass

class DomainUpdate(BaseModel):
    """Domain update model"""
    is_allowed: Optional[bool] = None
    auto_reply_enabled: Optional[bool] = None
    notes: Optional[str] = None

class Domain(DomainBase):
    """Domain response model"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Monitoring Models
class MonitoringSettings(BaseModel):
    """Monitoring settings model"""
    check_interval: int = 30
    enable_auto_reply: bool = True
    max_emails_per_check: int = 50
    
    @validator('check_interval')
    def validate_check_interval(cls, v):
        if v < 10:
            raise ValueError("Check interval must be at least 10 seconds")
        return v

class MonitoringStatus(BaseModel):
    """Monitoring status model"""
    is_running: bool
    check_interval: int
    last_check: Optional[datetime] = None
    processed_emails_count: int
    allowed_domains_count: int
    stats: Dict[str, Any] = {}

# Health Models
class ServiceHealth(BaseModel):
    """Service health model"""
    status: str
    details: Optional[Dict[str, Any]] = {}

class HealthStatus(BaseModel):
    """Overall health status model"""
    status: str
    timestamp: datetime
    services: Dict[str, ServiceHealth]

# Analytics Models
class EmailStats(BaseModel):
    """Email statistics model"""
    total_emails: int = 0
    replies_sent: int = 0
    auto_replies: int = 0
    manual_replies: int = 0
    failed_emails: int = 0
    success_rate: float = 0.0

class EmailAnalytics(BaseModel):
    """Email analytics model"""
    date: str
    stats: EmailStats

# AI Models
class AIReplyRequest(BaseModel):
    """AI reply generation request"""
    subject: str
    body: str
    sender: Optional[EmailStr] = None
    context: Optional[Dict[str, Any]] = {}

class AIReplyResponse(BaseModel):
    """AI reply generation response"""
    reply: str
    confidence: float = 1.0
    provider: str
    generated_at: datetime

class SentimentAnalysis(BaseModel):
    """Sentiment analysis model"""
    sentiment: SentimentType
    urgency: UrgencyLevel
    confidence: float
    keywords: List[str] = []

# Settings Models
class SystemSettings(BaseModel):
    """System settings model"""
    email_check_interval: int = Field(default=30, ge=10, le=3600, description="Email check interval in seconds")
    enable_auto_reply: bool = Field(default=True, description="Enable automatic email replies")
    max_emails_per_check: int = Field(default=50, ge=1, le=1000, description="Maximum emails to process per check")
    bulk_email_batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for bulk email sending")
    bulk_email_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between bulk email batches")
    rate_limit_requests: int = Field(default=100, ge=1, le=10000, description="Rate limit requests per period")
    rate_limit_period: int = Field(default=3600, ge=60, le=86400, description="Rate limit period in seconds")

# Template Models
class EmailTemplate(BaseModel):
    """Email template model"""
    id: int
    name: str
    subject: str
    body: str
    category: Optional[str] = None
    variables: List[str] = []
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class EmailTemplateCreate(BaseModel):
    """Email template creation model"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject template")
    body: str = Field(..., min_length=1, description="Email body template")
    category: Optional[str] = Field(None, max_length=100, description="Template category")
    variables: List[str] = Field(default=[], description="Template variable names")
    is_active: bool = Field(default=True, description="Whether template is active")

class EmailTemplateUpdate(BaseModel):
    """Email template update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    subject: Optional[str] = Field(None, min_length=1, max_length=500, description="Email subject template")
    body: Optional[str] = Field(None, min_length=1, description="Email body template")
    category: Optional[str] = Field(None, max_length=100, description="Template category")
    variables: Optional[List[str]] = Field(None, description="Template variable names")
    is_active: Optional[bool] = Field(None, description="Whether template is active")

class TemplateListResponse(BaseModel):
    """Template list response model"""
    success: bool
    message: str
    data: List[EmailTemplate]
    total: int
    skip: int
    limit: int

# Response Models
class StandardResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    page: int = 1
    per_page: int = 50
    pages: int
    
    @validator('pages', pre=True, always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        per_page = values.get('per_page', 50)
        return (total + per_page - 1) // per_page if per_page > 0 else 1

# Request Models
class EmailListRequest(BaseModel):
    """Email list request model"""
    limit: int = 50
    offset: int = 0
    mailbox: str = "INBOX"
    include_spam: bool = False
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        return v

class EmailSearchRequest(BaseModel):
    """Email search request model"""
    sender: Optional[str] = None
    subject: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    action: Optional[EmailAction] = None
    limit: int = 50
    offset: int = 0

class DomainCheckRequest(BaseModel):
    """Domain check request model"""
    domain: str
    
    @validator('domain')
    def validate_domain(cls, v):
        # Basic domain validation
        if not v or '.' not in v:
            raise ValueError("Invalid domain format")
        return v.lower().strip()

# Update models
class EmailLogUpdate(BaseModel):
    """Email log update model"""
    status: Optional[EmailStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

# Filter models
class DateRange(BaseModel):
    """Date range model"""
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError("End date must be after start date")
        return v
