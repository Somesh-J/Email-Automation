"""
Email processing routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..models import (
    EmailInbound, EmailReply, StandardResponse, EmailListRequest,
    EmailSearchRequest, AIReplyRequest, AIReplyResponse, SentimentAnalysis
)
from services import email_service, ai_service, sendgrid_service
from core.security import verify_api_key, check_rate_limit
from core.database import database_manager
from core.logger import email_logger

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ingest", response_model=StandardResponse)
async def ingest_email(
    email: EmailInbound,
    background_tasks: BackgroundTasks,
    auth_data: dict = Depends(check_rate_limit)
):
    """
    Ingest inbound email for processing
    
    This endpoint receives inbound emails and processes them according to
    configured rules including domain checking and auto-reply generation.
    """
    try:
        # Extract domain from sender
        domain = email.sender.split('@')[-1].lower()
        
        # Log email to database
        email_log_id = await database_manager.log_email({
            'sender': email.sender,
            'recipient': email.recipient,
            'subject': email.subject,
            'body': email.body,
            'action': 'received',
            'metadata': {
                'domain': domain,
                'timestamp': email.timestamp.isoformat() if email.timestamp else datetime.utcnow().isoformat()
            }
        })
        
        # Check if domain is allowed
        domains = await database_manager.get_domains(is_allowed=True)
        allowed_domains = {d['domain'] for d in domains}
        
        if domain not in allowed_domains:
            return StandardResponse(
                success=True,
                message=f"Email received but domain {domain} not allowed for auto-reply",
                data={"email_id": email_log_id, "domain_allowed": False}
            )
        
        # Add to background processing queue
        background_tasks.add_task(
            _process_email_background,
            email.dict(),
            email_log_id
        )
        
        return StandardResponse(
            success=True,
            message="Email received and queued for processing",
            data={"email_id": email_log_id, "domain_allowed": True}
        )
        
    except Exception as e:
        logger.error(f"Error ingesting email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=StandardResponse)
async def list_emails(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    mailbox: str = Query("INBOX"),
    include_spam: bool = Query(False),
    auth_data: dict = Depends(verify_api_key)
):
    """
    List emails from mailbox
    
    Retrieve emails from the specified mailbox with pagination support.
    """
    try:
        # Get emails from email service
        if mailbox.upper() == "UNREAD":
            emails = await email_service.get_unread_emails()
        else:
            emails = await email_service.get_recent_emails(
                hours=24,
                mailbox=mailbox,
                limit=limit
            )
        
        # Apply pagination
        total = len(emails)
        paginated_emails = emails[offset:offset + limit]
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(paginated_emails)} emails",
            data={
                "emails": paginated_emails,
                "total": total,
                "limit": limit,
                "offset": offset,
                "mailbox": mailbox
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{email_id}", response_model=StandardResponse)
async def get_email(
    email_id: str,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get specific email by ID
    """
    try:
        email_data = await email_service.fetch_email(email_id)
        
        if not email_data:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return StandardResponse(
            success=True,
            message="Email retrieved successfully",
            data=email_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply", response_model=StandardResponse)
async def send_reply(
    reply: EmailReply,
    auth_data: dict = Depends(check_rate_limit)
):
    """
    Send email reply
    
    Send a manual reply to an email address.
    """
    try:
        # Send email via SendGrid
        result = await sendgrid_service.send_email(
            to_email=reply.to_email,
            subject=reply.subject,
            content=reply.content,
            content_type=reply.content_type,
            from_name=reply.from_name
        )
        
        if result.get('success'):
            # Log reply to database
            await database_manager.log_email({
                'sender': result.get('from_email', 'system'),
                'recipient': reply.to_email,
                'subject': reply.subject,
                'body': reply.content,
                'action': 'replied',
                'reply_type': 'manual',
                'status': 'sent',
                'metadata': {
                    'message_id': result.get('message_id'),
                    'content_type': reply.content_type
                }
            })
            
            return StandardResponse(
                success=True,
                message="Reply sent successfully",
                data={
                    "message_id": result.get('message_id'),
                    "recipient": reply.to_email
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to send email'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-reply", response_model=AIReplyResponse)
async def generate_ai_reply(
    request: AIReplyRequest,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Generate AI-powered email reply
    
    Use AI to generate a professional reply based on the email content.
    """
    try:
        # Generate AI reply
        reply = await ai_service.generate_reply(
            subject=request.subject,
            body=request.body,
            sender=request.sender or "",
            context=request.context
        )
        
        if not reply:
            raise HTTPException(status_code=500, detail="Failed to generate AI reply")
        
        return AIReplyResponse(
            reply=reply,
            confidence=0.8,  # This could be dynamic based on AI provider
            provider=f"ai_{ai_service.__class__.__name__}",
            generated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-sentiment", response_model=SentimentAnalysis)
async def analyze_email_sentiment(
    request: AIReplyRequest,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Analyze email sentiment and urgency
    
    Use AI to analyze the sentiment and urgency level of an email.
    """
    try:
        analysis = await ai_service.analyze_email_sentiment(request.body)
        
        return SentimentAnalysis(
            sentiment=analysis.get('sentiment', 'neutral'),
            urgency=analysis.get('urgency', 'low'),
            confidence=analysis.get('confidence', 0.5),
            keywords=analysis.get('keywords', [])
        )
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=StandardResponse)
async def search_emails(
    sender: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Search emails with filters
    
    Search through email logs with various filters.
    """
    try:
        # Get email logs from database
        logs = await database_manager.get_email_logs(
            limit=limit,
            offset=offset,
            sender=sender,
            action=action,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter by subject if provided
        if subject:
            logs = [log for log in logs if subject.lower() in log.get('subject', '').lower()]
        
        return StandardResponse(
            success=True,
            message=f"Found {len(logs)} matching emails",
            data={
                "emails": logs,
                "filters": {
                    "sender": sender,
                    "subject": subject,
                    "action": action,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StandardResponse)
async def get_email_stats(
    days: int = Query(7, le=365),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get email statistics
    
    Retrieve email processing statistics for the specified period.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get logs for the period
        logs = await database_manager.get_email_logs(
            limit=10000,  # High limit to get all logs
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate statistics
        total_emails = len(logs)
        received_emails = len([log for log in logs if log.get('action') == 'received'])
        auto_replies = len([log for log in logs if log.get('action') == 'auto_replied'])
        manual_replies = len([log for log in logs if log.get('action') == 'replied'])
        failed_emails = len([log for log in logs if log.get('status') == 'failed'])
        
        success_rate = ((auto_replies + manual_replies) / received_emails * 100) if received_emails > 0 else 0
        
        stats = {
            "period_days": days,
            "total_emails": total_emails,
            "received_emails": received_emails,
            "auto_replies": auto_replies,
            "manual_replies": manual_replies,
            "total_replies": auto_replies + manual_replies,
            "failed_emails": failed_emails,
            "success_rate": round(success_rate, 2)
        }
        
        return StandardResponse(
            success=True,
            message=f"Email statistics for last {days} days",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/mark-read", response_model=StandardResponse)
async def mark_email_read(
    email_id: str,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Mark email as read
    """
    try:
        success = await email_service.mark_as_read(email_id)
        
        if success:
            return StandardResponse(
                success=True,
                message="Email marked as read",
                data={"email_id": email_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to mark email as read")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _process_email_background(email_data: dict, email_log_id: int):
    """Process email in background"""
    try:
        # This would implement the full email processing logic
        # Similar to what's in the email monitor service
        logger.info(f"Processing email {email_log_id} in background")
        
        # For now, just log that it was processed
        email_logger.log_email_received(
            email_data.get('sender', ''),
            email_data.get('subject', ''),
            str(email_log_id)
        )
        
    except Exception as e:
        logger.error(f"Error in background email processing: {e}")
