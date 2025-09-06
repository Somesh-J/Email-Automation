"""
Bulk email routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List
import logging
import uuid
from datetime import datetime

from ..models import BulkEmailRequest, BulkEmailJob, StandardResponse
from services import sendgrid_service
from core.security import verify_api_key, require_permissions, check_rate_limit
from core.database import database_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for job tracking (in production, use Redis or database)
bulk_jobs = {}

@router.post("/send", response_model=StandardResponse)
async def send_bulk_emails(
    request: BulkEmailRequest,
    background_tasks: BackgroundTasks,
    auth_data: dict = Depends(check_rate_limit)
):
    """
    Send bulk emails
    
    Send emails to multiple recipients with rate limiting and job tracking.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Prepare recipients
        recipients = []
        for recipient in request.recipients:
            if isinstance(recipient, str):
                recipients.append({"email": recipient, "data": {}})
            else:
                recipients.append({
                    "email": recipient.email,
                    "data": recipient.data or {}
                })
        
        # Create job record
        job = BulkEmailJob(
            job_id=job_id,
            name=f"Bulk email {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            status="queued",
            recipients_count=len(recipients),
            created_at=datetime.utcnow()
        )
        
        # Store job in memory (in production, use database)
        bulk_jobs[job_id] = job.dict()
        
        # Add to background processing
        background_tasks.add_task(
            _process_bulk_email_job,
            job_id=job_id,
            recipients=recipients,
            subject=request.subject,
            content=request.content,
            content_type=request.content_type,
            from_name=request.from_name,
            batch_size=request.batch_size,
            delay=request.delay
        )
        
        return StandardResponse(
            success=True,
            message=f"Bulk email job {job_id} queued successfully",
            data={
                "job_id": job_id,
                "recipients_count": len(recipients),
                "status": "queued"
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending bulk emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=StandardResponse)
async def list_bulk_jobs(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    auth_data: dict = Depends(verify_api_key)
):
    """
    List bulk email jobs
    
    Retrieve list of bulk email jobs with their status.
    """
    try:
        # Get jobs from storage (paginated)
        jobs_list = list(bulk_jobs.values())
        jobs_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(paginated_jobs)} bulk email jobs",
            data={
                "jobs": paginated_jobs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing bulk jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=StandardResponse)
async def get_bulk_job(
    job_id: str,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get bulk email job details
    
    Retrieve details for a specific bulk email job.
    """
    try:
        job = bulk_jobs.get(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return StandardResponse(
            success=True,
            message="Bulk email job retrieved successfully",
            data=job
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bulk job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}", response_model=StandardResponse)
async def cancel_bulk_job(
    job_id: str,
    auth_data: dict = Depends(require_permissions(["bulk_email_manage"]))
):
    """
    Cancel bulk email job
    
    Cancel a running or queued bulk email job.
    """
    try:
        job = bulk_jobs.get(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job['status']}")
        
        # Update job status
        job["status"] = "cancelled"
        job["updated_at"] = datetime.utcnow().isoformat()
        bulk_jobs[job_id] = job
        
        return StandardResponse(
            success=True,
            message=f"Bulk email job {job_id} cancelled successfully",
            data={"job_id": job_id, "status": "cancelled"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling bulk job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StandardResponse)
async def get_bulk_email_stats(
    days: int = Query(7, le=365),
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get bulk email statistics
    
    Retrieve statistics for bulk email operations.
    """
    try:
        # Calculate stats from stored jobs
        total_jobs = len(bulk_jobs)
        completed_jobs = len([job for job in bulk_jobs.values() if job["status"] == "completed"])
        failed_jobs = len([job for job in bulk_jobs.values() if job["status"] == "failed"])
        running_jobs = len([job for job in bulk_jobs.values() if job["status"] == "running"])
        queued_jobs = len([job for job in bulk_jobs.values() if job["status"] == "queued"])
        
        # Calculate email counts
        total_emails_sent = sum(job.get("sent_count", 0) for job in bulk_jobs.values())
        total_emails_failed = sum(job.get("failed_count", 0) for job in bulk_jobs.values())
        total_recipients = sum(job.get("recipients_count", 0) for job in bulk_jobs.values())
        
        success_rate = (total_emails_sent / total_recipients * 100) if total_recipients > 0 else 0
        
        stats = {
            "period_days": days,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": running_jobs,
            "queued_jobs": queued_jobs,
            "total_emails_sent": total_emails_sent,
            "total_emails_failed": total_emails_failed,
            "total_recipients": total_recipients,
            "success_rate": round(success_rate, 2)
        }
        
        return StandardResponse(
            success=True,
            message=f"Bulk email statistics for last {days} days",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting bulk email stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-recipients", response_model=StandardResponse)
async def validate_recipients(
    recipients: List[str],
    auth_data: dict = Depends(verify_api_key)
):
    """
    Validate email recipients
    
    Validate a list of email addresses before sending.
    """
    try:
        validation_results = []
        
        for email in recipients:
            # Basic email validation
            if "@" in email and "." in email.split("@")[-1]:
                validation_results.append({
                    "email": email,
                    "valid": True,
                    "reason": "Valid format"
                })
            else:
                validation_results.append({
                    "email": email,
                    "valid": False,
                    "reason": "Invalid format"
                })
        
        valid_count = len([r for r in validation_results if r["valid"]])
        invalid_count = len(validation_results) - valid_count
        
        return StandardResponse(
            success=True,
            message=f"Validated {len(recipients)} recipients",
            data={
                "results": validation_results,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "total_count": len(recipients)
            }
        )
        
    except Exception as e:
        logger.error(f"Error validating recipients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _process_bulk_email_job(
    job_id: str,
    recipients: List[dict],
    subject: str,
    content: str,
    content_type: str = "text/plain",
    from_name: str = None,
    batch_size: int = 10,
    delay: float = 1.0
):
    """Process bulk email job in background"""
    try:
        # Update job status
        if job_id in bulk_jobs:
            bulk_jobs[job_id]["status"] = "running"
            bulk_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting bulk email job {job_id} with {len(recipients)} recipients")
        
        # Send bulk emails
        result = await sendgrid_service.send_bulk_emails(
            recipients=recipients,
            subject=subject,
            content=content,
            content_type=content_type,
            from_name=from_name,
            batch_size=batch_size,
            delay=delay
        )
        
        # Update job with results
        if job_id in bulk_jobs:
            bulk_jobs[job_id].update({
                "status": "completed" if result.get("success") else "failed",
                "sent_count": result.get("sent", 0),
                "failed_count": result.get("failed", 0),
                "progress_percentage": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result
            })
        
        logger.info(f"Bulk email job {job_id} completed: {result}")
        
    except Exception as e:
        logger.error(f"Error processing bulk email job {job_id}: {e}")
        
        # Update job with error
        if job_id in bulk_jobs:
            bulk_jobs[job_id].update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
