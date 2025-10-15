"""
Database management for Email Automation API
Supports both MongoDB (using Beanie) for document storage
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from core.config import settings
from core.mongo_models import (
    EmailMongo, DomainMongo, EmailTemplateMongo,
    BulkEmailJobMongo, MonitoringStatusMongo, APIKeyMongo,
    SystemSettingsMongo, EmailLogMongo
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for MongoDB operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to MongoDB database"""
        try:
            if self.is_connected:
                logger.info("Already connected to MongoDB")
                return
            
            # Build MongoDB connection string
            if settings.MONGO_URL:
                connection_string = settings.MONGO_URL
            else:
                if settings.MONGO_USERNAME and settings.MONGO_PASSWORD:
                    auth_part = f"{settings.MONGO_USERNAME}:{settings.MONGO_PASSWORD}@"
                else:
                    auth_part = ""
                
                ssl_part = "?ssl=true" if settings.MONGO_USE_SSL else ""
                connection_string = f"mongodb://{auth_part}{settings.MONGO_HOST}:{settings.MONGO_PORT}/{ssl_part}"
            
            # Create MongoDB client
            self.client = AsyncIOMotorClient(connection_string)
            self.db = self.client[settings.MONGO_DB_NAME]
            
            # Initialize Beanie with all document models
            await init_beanie(
                database=self.db,
                document_models=[
                    EmailMongo,
                    DomainMongo,
                    EmailTemplateMongo,
                    BulkEmailJobMongo,
                    MonitoringStatusMongo,
                    APIKeyMongo,
                    SystemSettingsMongo,
                    EmailLogMongo
                ]
            )
            
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB: {settings.MONGO_DB_NAME}")
            
            # Initialize default data
            await self.init_default_data()
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.is_connected = False
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    async def init_default_data(self):
        """Initialize default data in database"""
        try:
            # Initialize default domains
            for domain in settings.DEFAULT_ALLOWED_DOMAINS:
                existing = await DomainMongo.find_one(DomainMongo.domain == domain)
                if not existing:
                    domain_doc = DomainMongo(
                        domain=domain,
                        is_allowed=True,
                        is_blocked=False,
                        auto_reply_enabled=True,
                        description=f"Default allowed domain: {domain}"
                    )
                    await domain_doc.insert()
                    logger.info(f"Added default domain: {domain}")
            
            # Initialize blocked domains
            for domain in settings.BLOCKED_DOMAINS:
                existing = await DomainMongo.find_one(DomainMongo.domain == domain)
                if not existing:
                    domain_doc = DomainMongo(
                        domain=domain,
                        is_allowed=False,
                        is_blocked=True,
                        auto_reply_enabled=False,
                        description=f"Blocked domain: {domain}"
                    )
                    await domain_doc.insert()
                    logger.info(f"Added blocked domain: {domain}")
            
            # Initialize default email template
            existing_template = await EmailTemplateMongo.find_one(
                EmailTemplateMongo.name == "default_auto_reply"
            )
            if not existing_template:
                template = EmailTemplateMongo(
                    name="default_auto_reply",
                    subject="Re: {subject}",
                    body="Thank you for your email. We have received your message and will respond shortly.\n\nBest regards,\n{from_name}",
                    category="auto_reply",
                    variables=["subject", "from_name"],
                    is_active=True,
                    description="Default auto-reply template"
                )
                await template.insert()
                logger.info("Added default email template")
            
            # Initialize monitoring status
            existing_status = await MonitoringStatusMongo.find_one()
            if not existing_status:
                status = MonitoringStatusMongo(
                    service_name="email_monitor",
                    is_running=False,
                    start_time=None,
                    last_check=None,
                    emails_processed=0,
                    emails_failed=0
                )
                await status.insert()
                logger.info("Initialized monitoring status")
            
            # Initialize default API keys if provided
            if settings.VALID_API_KEYS:
                for api_key in settings.VALID_API_KEYS:
                    existing_key = await APIKeyMongo.find_one(APIKeyMongo.key_hash == api_key)
                    if not existing_key:
                        key_doc = APIKeyMongo(
                            name=f"Default Key {api_key[:8]}",
                            key_hash=api_key,
                            is_active=True,
                            description="Default API key"
                        )
                        await key_doc.insert()
                        logger.info(f"Added default API key: {api_key[:8]}...")
            
            logger.info("Default data initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing default data: {e}")
    
    # Email Operations
    async def log_email(self, email_data: Dict[str, Any]) -> str:
        """Log email to database"""
        try:
            email_log = EmailLogMongo(**email_data)
            await email_log.insert()
            return str(email_log.id)
        except Exception as e:
            logger.error(f"Error logging email: {e}")
            raise
    
    async def get_emails(self, skip: int = 0, limit: int = 50, 
                        filters: Optional[Dict] = None) -> List[Dict]:
        """Get emails with pagination and filters"""
        try:
            query = EmailMongo.find()
            
            if filters:
                if 'sender' in filters:
                    query = query.find(EmailMongo.sender == filters['sender'])
                if 'status' in filters:
                    query = query.find(EmailMongo.status == filters['status'])
                if 'date_from' in filters:
                    query = query.find(EmailMongo.date_received >= filters['date_from'])
                if 'date_to' in filters:
                    query = query.find(EmailMongo.date_received <= filters['date_to'])
            
            emails = await query.skip(skip).limit(limit).sort("-date_received").to_list()
            return [email.dict() for email in emails]
            
        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            return []
    
    # Domain Operations
    async def get_domains(self, is_allowed: Optional[bool] = None, 
                         is_blocked: Optional[bool] = None) -> List[Dict]:
        """Get domains with optional filters"""
        try:
            query = DomainMongo.find()
            
            if is_allowed is not None:
                query = query.find(DomainMongo.is_allowed == is_allowed)
            if is_blocked is not None:
                query = query.find(DomainMongo.is_blocked == is_blocked)
            
            domains = await query.to_list()
            return [domain.dict() for domain in domains]
            
        except Exception as e:
            logger.error(f"Error getting domains: {e}")
            return []
    
    async def get_domain(self, domain: str) -> Optional[Dict]:
        """Get specific domain"""
        try:
            domain_doc = await DomainMongo.find_one(DomainMongo.domain == domain)
            return domain_doc.dict() if domain_doc else None
        except Exception as e:
            logger.error(f"Error getting domain: {e}")
            return None
    
    async def create_domain(self, domain_data: Dict[str, Any]) -> str:
        """Create new domain"""
        try:
            domain = DomainMongo(**domain_data)
            await domain.insert()
            return str(domain.id)
        except Exception as e:
            logger.error(f"Error creating domain: {e}")
            raise
    
    async def update_domain(self, domain_name: str, update_data: Dict[str, Any]) -> bool:
        """Update domain"""
        try:
            domain = await DomainMongo.find_one(DomainMongo.domain == domain_name)
            if domain:
                for key, value in update_data.items():
                    setattr(domain, key, value)
                domain.updated_at = datetime.utcnow()
                await domain.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating domain: {e}")
            return False
    
    async def delete_domain(self, domain_name: str) -> bool:
        """Delete domain"""
        try:
            domain = await DomainMongo.find_one(DomainMongo.domain == domain_name)
            if domain:
                await domain.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting domain: {e}")
            return False
    
    # Template Operations
    async def get_templates(self, category: Optional[str] = None, 
                          is_active: Optional[bool] = None) -> List[Dict]:
        """Get email templates"""
        try:
            query = EmailTemplateMongo.find()
            
            if category:
                query = query.find(EmailTemplateMongo.category == category)
            if is_active is not None:
                query = query.find(EmailTemplateMongo.is_active == is_active)
            
            templates = await query.to_list()
            return [template.dict() for template in templates]
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    async def get_template(self, template_id: str) -> Optional[Dict]:
        """Get specific template"""
        try:
            template = await EmailTemplateMongo.get(template_id)
            return template.dict() if template else None
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None
    
    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create email template"""
        try:
            template = EmailTemplateMongo(**template_data)
            await template.insert()
            return str(template.id)
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def update_template(self, template_id: str, update_data: Dict[str, Any]) -> bool:
        """Update template"""
        try:
            template = await EmailTemplateMongo.get(template_id)
            if template:
                for key, value in update_data.items():
                    setattr(template, key, value)
                template.updated_at = datetime.utcnow()
                await template.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return False
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        try:
            template = await EmailTemplateMongo.get(template_id)
            if template:
                await template.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    # Bulk Email Job Operations
    async def create_bulk_job(self, job_data: Dict[str, Any]) -> str:
        """Create bulk email job"""
        try:
            job = BulkEmailJobMongo(**job_data)
            await job.insert()
            return str(job.id)
        except Exception as e:
            logger.error(f"Error creating bulk job: {e}")
            raise
    
    async def get_bulk_job(self, job_id: str) -> Optional[Dict]:
        """Get bulk email job"""
        try:
            job = await BulkEmailJobMongo.get(job_id)
            return job.dict() if job else None
        except Exception as e:
            logger.error(f"Error getting bulk job: {e}")
            return None
    
    async def update_bulk_job(self, job_id: str, update_data: Dict[str, Any]) -> bool:
        """Update bulk email job"""
        try:
            job = await BulkEmailJobMongo.get(job_id)
            if job:
                for key, value in update_data.items():
                    setattr(job, key, value)
                job.updated_at = datetime.utcnow()
                await job.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating bulk job: {e}")
            return False
    
    # Monitoring Operations
    async def get_monitoring_status(self) -> Optional[Dict]:
        """Get monitoring status"""
        try:
            status = await MonitoringStatusMongo.find_one()
            return status.dict() if status else None
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return None
    
    async def update_monitoring_status(self, update_data: Dict[str, Any]) -> bool:
        """Update monitoring status"""
        try:
            status = await MonitoringStatusMongo.find_one()
            if status:
                for key, value in update_data.items():
                    setattr(status, key, value)
                await status.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating monitoring status: {e}")
            return False
    
    # System Settings Operations
    async def get_setting(self, key: str) -> Optional[Any]:
        """Get system setting"""
        try:
            setting = await SystemSettingsMongo.find_one(SystemSettingsMongo.key == key)
            return setting.value if setting else None
        except Exception as e:
            logger.error(f"Error getting setting: {e}")
            return None
    
    async def set_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set system setting"""
        try:
            setting = await SystemSettingsMongo.find_one(SystemSettingsMongo.key == key)
            if setting:
                setting.value = value
                if description:
                    setting.description = description
                setting.updated_at = datetime.utcnow()
                await setting.save()
            else:
                setting = SystemSettingsMongo(
                    key=key,
                    value=value,
                    description=description or f"Setting: {key}"
                )
                await setting.insert()
            return True
        except Exception as e:
            logger.error(f"Error setting value: {e}")
            return False
    
    # Analytics Operations
    async def get_email_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get email statistics"""
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            total_emails = await EmailMongo.find(
                EmailMongo.date_received >= start_date
            ).count()
            
            replied_emails = await EmailMongo.find(
                EmailMongo.date_received >= start_date,
                EmailMongo.status == "replied"
            ).count()
            
            ai_replies = await EmailMongo.find(
                EmailMongo.date_received >= start_date,
                EmailMongo.ai_reply_sent == True
            ).count()
            
            return {
                "total_emails": total_emails,
                "replied_emails": replied_emails,
                "ai_replies": ai_replies,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            # Check connection
            if not self.is_connected or not self.client:
                return {
                    "status": "unhealthy",
                    "database": "mongodb",
                    "connected": False
                }
            
            # Perform a simple query
            await self.db.command("ping")
            
            # Get collection counts
            email_count = await EmailMongo.count()
            domain_count = await DomainMongo.count()
            template_count = await EmailTemplateMongo.count()
            
            return {
                "status": "healthy",
                "database": "mongodb",
                "connected": True,
                "database_name": settings.MONGO_DB_NAME,
                "collections": {
                    "emails": email_count,
                    "domains": domain_count,
                    "templates": template_count
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "mongodb",
                "error": str(e)
            }


# Create global database manager instance
database_manager = DatabaseManager()


# Dependency for getting database
async def get_db():
    """Dependency for getting database connection"""
    if not database_manager.is_connected:
        await database_manager.connect()
    return database_manager
