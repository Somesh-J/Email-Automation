"""
Configuration management for Email Automation API
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    """Application settings"""
    
    # App Configuration
    APP_NAME: str = "Email Automation API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API Configuration
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "email_automation"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # MongoDB Configuration
    MONGO_URL: Optional[str] = None
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB_NAME: str = "email_automation"
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_AUTH_DB: str = "admin"
    MONGO_USE_SSL: bool = False
    
    # Database Selection
    USE_MONGODB: bool = False  # Set to True to use MongoDB instead of PostgreSQL
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Email Configuration - IMAP
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USE_SSL: bool = True
    IMAP_USERNAME: str = ""
    IMAP_PASSWORD: str = ""
    
    # Email Configuration - SMTP/SendGrid
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@example.com"
    FROM_NAME: str = "Email Automation"
    
    # AI Configuration
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"  # gemini, openai, or custom
    
    # Monitoring Configuration
    AUTO_START_MONITORING: bool = False
    EMAIL_CHECK_INTERVAL: int = 30  # seconds
    MAX_EMAILS_PER_CHECK: int = 50
    ENABLE_AUTO_REPLY: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # seconds (1 hour)
    
    # Bulk Email Configuration
    BULK_EMAIL_BATCH_SIZE: int = 10
    BULK_EMAIL_DELAY: float = 1.0  # seconds between batches
    MAX_BULK_RECIPIENTS: int = 1000
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security Configuration
    API_KEY_HEADER: str = "X-API-Key"
    VALID_API_KEYS: List[str] = []
    
    # Domain Configuration
    DEFAULT_ALLOWED_DOMAINS: List[str] = ["gmail.com", "outlook.com"]
    BLOCKED_DOMAINS: List[str] = []
    
    # Cache Configuration
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000
    
    @validator('DATABASE_URL', pre=True)
    def build_database_url(cls, v, values):
        """Build database URL if not provided"""
        if v:
            return v
        
        user = values.get('DB_USER', 'postgres')
        password = values.get('DB_PASSWORD', 'password')
        host = values.get('DB_HOST', 'localhost')
        port = values.get('DB_PORT', 5432)
        db_name = values.get('DB_NAME', 'email_automation')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    @validator('MONGO_URL', pre=True)
    def build_mongo_url(cls, v, values):
        """Build MongoDB URL if not provided"""
        if v:
            return v
        
        host = values.get('MONGO_HOST', 'localhost')
        port = values.get('MONGO_PORT', 27017)
        username = values.get('MONGO_USERNAME')
        password = values.get('MONGO_PASSWORD')
        auth_db = values.get('MONGO_AUTH_DB', 'admin')
        use_ssl = values.get('MONGO_USE_SSL', False)
        
        if username and password:
            auth_string = f"{username}:{password}@"
            auth_params = f"?authSource={auth_db}"
        else:
            auth_string = ""
            auth_params = ""
        
        ssl_param = "&ssl=true" if use_ssl else ""
        
        return f"mongodb://{auth_string}{host}:{port}/{auth_params}{ssl_param}"
    
    @validator('REDIS_URL', pre=True)
    def build_redis_url(cls, v, values):
        """Build Redis URL if not provided"""
        if v:
            return v
        
        host = values.get('REDIS_HOST', 'localhost')
        port = values.get('REDIS_PORT', 6379)
        db = values.get('REDIS_DB', 0)
        password = values.get('REDIS_PASSWORD')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    @validator('VALID_API_KEYS', pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from environment variable"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(',') if key.strip()]
        return v or []
    
    @validator('ALLOWED_ORIGINS', pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from environment variable"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v or ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Email provider configurations
EMAIL_PROVIDERS = {
    "gmail": {
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_ssl": True
    },
    "outlook": {
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "smtp_server": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "use_ssl": True
    },
    "yahoo": {
        "imap_server": "imap.mail.yahoo.com",
        "imap_port": 993,
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_ssl": True
    }
}

# AI provider configurations
AI_PROVIDERS = {
    "gemini": {
        "model": "gemini-pro",
        "max_tokens": 1000,
        "temperature": 0.7
    },
    "openai": {
        "model": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.7
    }
}

# Email templates
EMAIL_TEMPLATES = {
    "default_auto_reply": """
    Thank you for your email. We have received your message and will respond within 24 hours.
    
    Best regards,
    {sender_name}
    """,
    
    "support_auto_reply": """
    Thank you for contacting our support team. We have received your request and will get back to you shortly.
    
    Ticket ID: {ticket_id}
    
    Best regards,
    Support Team
    """,
    
    "sales_auto_reply": """
    Thank you for your interest in our services. A member of our sales team will contact you within 1 business day.
    
    Best regards,
    Sales Team
    """
}
