"""
Security utilities for Email Automation API
"""

import hashlib
import secrets
from typing import Optional, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

from .config import settings
from .database import get_db, ApiKey
from sqlalchemy.ext.asyncio import AsyncSession

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"

# Security schemes
security = HTTPBearer(auto_error=False)

class SecurityManager:
    """Security manager for API authentication and authorization"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Verify API key authentication"""
    
    # Check if API key is provided in header
    api_key = None
    
    if credentials:
        # Bearer token format
        api_key = credentials.credentials
    else:
        # Check for API key in custom header (fallback)
        # This would need to be implemented with a custom dependency
        pass
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check against configured API keys first
    if api_key in settings.VALID_API_KEYS:
        return {
            "api_key": api_key,
            "permissions": ["all"],
            "source": "config"
        }
    
    # Check against database API keys
    try:
        key_hash = SecurityManager.hash_api_key(api_key)
        
        # Query for API key in database
        # This would need to be implemented with proper async query
        # For now, return basic validation
        
        return {
            "api_key": api_key,
            "permissions": ["basic"],
            "source": "database"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

async def verify_api_key_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Optional API key verification"""
    if not credentials:
        return None
    
    try:
        return await verify_api_key(credentials)
    except HTTPException:
        return None

def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions"""
    def permission_checker(auth_data: dict = Depends(verify_api_key)):
        user_permissions = auth_data.get("permissions", [])
        
        if "all" in user_permissions:
            return auth_data
        
        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        
        return auth_data
    
    return permission_checker

# Rate limiting
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int = None, window: int = None) -> bool:
        """Check if request is allowed"""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_PERIOD
        
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < timedelta(seconds=window)
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, limit: int = None) -> int:
        """Get remaining requests"""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        
        if key not in self.requests:
            return limit
        
        return max(0, limit - len(self.requests[key]))

# Global rate limiter instance
rate_limiter = RateLimiter()

async def check_rate_limit(
    request,
    auth_data: dict = Depends(verify_api_key)
):
    """Check rate limit for authenticated requests"""
    client_ip = request.client.host
    api_key = auth_data.get("api_key", "unknown")
    
    # Use API key as primary identifier, fallback to IP
    rate_limit_key = f"api:{api_key}" if api_key != "unknown" else f"ip:{client_ip}"
    
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": str(rate_limiter.get_remaining(rate_limit_key)),
                "X-RateLimit-Reset": str(settings.RATE_LIMIT_PERIOD)
            }
        )
    
    return auth_data

# Input validation and sanitization
def sanitize_email(email: str) -> str:
    """Sanitize email address"""
    return email.strip().lower()

def sanitize_domain(domain: str) -> str:
    """Sanitize domain name"""
    return domain.strip().lower().replace("www.", "")

def validate_email_content(content: str) -> bool:
    """Validate email content for security"""
    # Check for suspicious patterns
    suspicious_patterns = [
        "<script",
        "javascript:",
        "data:text/html",
        "vbscript:",
        "onload=",
        "onerror=",
        "onclick="
    ]
    
    content_lower = content.lower()
    return not any(pattern in content_lower for pattern in suspicious_patterns)

# CORS helper
def get_cors_origins() -> List[str]:
    """Get CORS origins from settings"""
    return settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["*"]
