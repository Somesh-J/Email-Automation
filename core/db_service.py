"""
Database service adapter for unified access to PostgreSQL and MongoDB
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

from core.config import settings
from core.database import get_db, get_mongo_db

if settings.USE_MONGODB:
    from core.mongo_models import (
        EmailMongo, DomainMongo, EmailTemplateMongo, 
        BulkEmailJobMongo, MonitoringStatusMongo, APIKeyMongo,
        SystemSettingsMongo, EmailLogMongo
    )
else:
    from core.database import (
        EmailDB, Domain, EmailTemplateDB, BulkEmailJobDB, 
        MonitoringStatus, ApiKeyDB, SystemSettingsDB, EmailLog
    )

logger = logging.getLogger(__name__)

class DatabaseService:
    """Unified database service for both PostgreSQL and MongoDB"""
    
    def __init__(self):
        self.use_mongodb = settings.USE_MONGODB
    
    # Email Operations
    async def create_email(self, email_data: Dict[str, Any]) -> str:
        """Create a new email record"""
        try:
            if self.use_mongodb:
                email = EmailMongo(**email_data)
                await email.insert()
                return str(email.id)
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    email = EmailDB(**email_data)
                    session.add(email)
                    await session.commit()
                    await session.refresh(email)
                    return str(email.id)
        except Exception as e:
            logger.error(f"Error creating email: {e}")
            raise
    
    async def get_emails(self, skip: int = 0, limit: int = 50, filters: Optional[Dict] = None) -> List[Dict]:
        """Get emails with pagination and filters"""
        try:
            if self.use_mongodb:
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
                
                emails = await query.skip(skip).limit(limit).to_list()
                return [email.dict() for email in emails]
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    query = session.query(EmailDB)
                    if filters:
                        if 'sender' in filters:
                            query = query.filter(EmailDB.sender == filters['sender'])
                        if 'status' in filters:
                            query = query.filter(EmailDB.status == filters['status'])
                        if 'date_from' in filters:
                            query = query.filter(EmailDB.date_received >= filters['date_from'])
                        if 'date_to' in filters:
                            query = query.filter(EmailDB.date_received <= filters['date_to'])
                    
                    result = await session.execute(query.offset(skip).limit(limit))
                    emails = result.scalars().all()
                    return [{"id": e.id, "email_id": e.email_id, "sender": e.sender, 
                            "subject": e.subject, "status": e.status, "date_received": e.date_received} for e in emails]
        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            raise
    
    async def update_email(self, email_id: str, update_data: Dict[str, Any]) -> bool:
        """Update email record"""
        try:
            if self.use_mongodb:
                email = await EmailMongo.find_one(EmailMongo.email_id == email_id)
                if email:
                    for key, value in update_data.items():
                        setattr(email, key, value)
                    email.updated_at = datetime.utcnow()
                    await email.save()
                    return True
                return False
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT * FROM emails WHERE email_id = :email_id",
                        {"email_id": email_id}
                    )
                    email = result.fetchone()
                    if email:
                        for key, value in update_data.items():
                            await session.execute(
                                f"UPDATE emails SET {key} = :value, updated_at = NOW() WHERE email_id = :email_id",
                                {"value": value, "email_id": email_id}
                            )
                        await session.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error updating email: {e}")
            raise
    
    # Domain Operations
    async def create_domain(self, domain_data: Dict[str, Any]) -> str:
        """Create a new domain record"""
        try:
            if self.use_mongodb:
                domain = DomainMongo(**domain_data)
                await domain.insert()
                return str(domain.id)
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    domain = Domain(**domain_data)
                    session.add(domain)
                    await session.commit()
                    await session.refresh(domain)
                    return str(domain.id)
        except Exception as e:
            logger.error(f"Error creating domain: {e}")
            raise
    
    async def get_domains(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get domains with pagination"""
        try:
            if self.use_mongodb:
                domains = await DomainMongo.find().skip(skip).limit(limit).to_list()
                return [domain.dict() for domain in domains]
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT * FROM domains ORDER BY created_at DESC OFFSET :skip LIMIT :limit",
                        {"skip": skip, "limit": limit}
                    )
                    domains = result.fetchall()
                    return [{"id": d.id, "domain": d.domain, "is_allowed": d.is_allowed, 
                            "is_blocked": d.is_blocked, "created_at": d.created_at} for d in domains]
        except Exception as e:
            logger.error(f"Error getting domains: {e}")
            raise
    
    async def get_domain_by_name(self, domain_name: str) -> Optional[Dict]:
        """Get domain by name"""
        try:
            if self.use_mongodb:
                domain = await DomainMongo.find_one(DomainMongo.domain == domain_name)
                return domain.dict() if domain else None
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT * FROM domains WHERE domain = :domain",
                        {"domain": domain_name}
                    )
                    domain = result.fetchone()
                    return {"id": domain.id, "domain": domain.domain, "is_allowed": domain.is_allowed} if domain else None
        except Exception as e:
            logger.error(f"Error getting domain: {e}")
            raise
    
    # Template Operations
    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new email template"""
        try:
            if self.use_mongodb:
                template = EmailTemplateMongo(**template_data)
                await template.insert()
                return str(template.id)
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    template = EmailTemplateDB(**template_data)
                    session.add(template)
                    await session.commit()
                    await session.refresh(template)
                    return str(template.id)
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_templates(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Dict]:
        """Get email templates"""
        try:
            if self.use_mongodb:
                query = EmailTemplateMongo.find()
                if active_only:
                    query = query.find(EmailTemplateMongo.is_active == True)
                templates = await query.skip(skip).limit(limit).to_list()
                return [template.dict() for template in templates]
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    where_clause = "WHERE is_active = true" if active_only else ""
                    result = await session.execute(
                        f"SELECT * FROM email_templates {where_clause} ORDER BY created_at DESC OFFSET :skip LIMIT :limit",
                        {"skip": skip, "limit": limit}
                    )
                    templates = result.fetchall()
                    return [{"id": t.id, "name": t.name, "subject": t.subject, 
                            "body": t.body, "category": t.category, "is_active": t.is_active} for t in templates]
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            raise
    
    # Bulk Email Job Operations
    async def create_bulk_job(self, job_data: Dict[str, Any]) -> str:
        """Create a bulk email job"""
        try:
            if self.use_mongodb:
                job = BulkEmailJobMongo(**job_data)
                await job.insert()
                return str(job.id)
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    job = BulkEmailJobDB(**job_data)
                    session.add(job)
                    await session.commit()
                    await session.refresh(job)
                    return str(job.id)
        except Exception as e:
            logger.error(f"Error creating bulk job: {e}")
            raise
    
    async def get_bulk_jobs(self, skip: int = 0, limit: int = 50) -> List[Dict]:
        """Get bulk email jobs"""
        try:
            if self.use_mongodb:
                jobs = await BulkEmailJobMongo.find().skip(skip).limit(limit).to_list()
                return [job.dict() for job in jobs]
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT * FROM bulk_email_jobs ORDER BY created_at DESC OFFSET :skip LIMIT :limit",
                        {"skip": skip, "limit": limit}
                    )
                    jobs = result.fetchall()
                    return [{"id": j.id, "job_id": j.job_id, "name": j.name, 
                            "status": j.status, "total_emails": j.total_emails, 
                            "sent_count": j.sent_count, "created_at": j.created_at} for j in jobs]
        except Exception as e:
            logger.error(f"Error getting bulk jobs: {e}")
            raise
    
    # Monitoring Operations
    async def get_monitoring_status(self, service_name: str) -> Optional[Dict]:
        """Get monitoring status for a service"""
        try:
            if self.use_mongodb:
                status = await MonitoringStatusMongo.find_one(MonitoringStatusMongo.service_name == service_name)
                return status.dict() if status else None
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT * FROM monitoring_status WHERE service_name = :service",
                        {"service": service_name}
                    )
                    status = result.fetchone()
                    return {"service_name": status.service_name, "is_active": status.is_active, 
                            "last_check": status.last_check, "health_status": status.health_status} if status else None
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            raise
    
    async def update_monitoring_status(self, service_name: str, status_data: Dict[str, Any]) -> bool:
        """Update monitoring status"""
        try:
            if self.use_mongodb:
                status = await MonitoringStatusMongo.find_one(MonitoringStatusMongo.service_name == service_name)
                if status:
                    for key, value in status_data.items():
                        setattr(status, key, value)
                    status.updated_at = datetime.utcnow()
                    await status.save()
                    return True
                return False
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    # Update the monitoring status
                    update_pairs = [f"{key} = :{key}" for key in status_data.keys()]
                    update_clause = ", ".join(update_pairs)
                    status_data['service'] = service_name
                    
                    result = await session.execute(
                        f"UPDATE monitoring_status SET {update_clause}, updated_at = NOW() WHERE service_name = :service",
                        status_data
                    )
                    await session.commit()
                    return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating monitoring status: {e}")
            raise
    
    # Analytics Operations
    async def get_email_stats(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get email statistics"""
        try:
            if self.use_mongodb:
                query = EmailMongo.find()
                if date_from:
                    query = query.find(EmailMongo.date_received >= date_from)
                if date_to:
                    query = query.find(EmailMongo.date_received <= date_to)
                
                emails = await query.to_list()
                total = len(emails)
                replied = sum(1 for e in emails if e.status == "replied")
                auto_replied = sum(1 for e in emails if e.ai_reply_sent)
                
                return {
                    "total_emails": total,
                    "replied_emails": replied,
                    "auto_replies": auto_replied,
                    "success_rate": (replied / total * 100) if total > 0 else 0
                }
            else:
                from core.database import database_manager
                async with database_manager.get_session() as session:
                    where_conditions = []
                    params = {}
                    
                    if date_from:
                        where_conditions.append("date_received >= :date_from")
                        params['date_from'] = date_from
                    if date_to:
                        where_conditions.append("date_received <= :date_to")
                        params['date_to'] = date_to
                    
                    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                    
                    result = await session.execute(
                        f"""
                        SELECT 
                            COUNT(*) as total_emails,
                            COUNT(CASE WHEN status = 'replied' THEN 1 END) as replied_emails,
                            COUNT(CASE WHEN ai_reply_sent = true THEN 1 END) as auto_replies
                        FROM emails {where_clause}
                        """,
                        params
                    )
                    stats = result.fetchone()
                    total = stats.total_emails or 0
                    replied = stats.replied_emails or 0
                    auto_replies = stats.auto_replies or 0
                    
                    return {
                        "total_emails": total,
                        "replied_emails": replied,
                        "auto_replies": auto_replies,
                        "success_rate": (replied / total * 100) if total > 0 else 0
                    }
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            raise

# Global database service instance
db_service = DatabaseService()
