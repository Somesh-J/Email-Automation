"""
Domain management routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from ..models import DomainCreate, DomainUpdate, Domain, StandardResponse
from core.security import verify_api_key, require_permissions
from core.database import database_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=StandardResponse)
async def list_domains(
    is_allowed: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    auth_data: dict = Depends(verify_api_key)
):
    """
    List all domains
    
    Retrieve all domains with optional filtering by allowed status.
    """
    try:
        domains = await database_manager.get_domains(is_allowed=is_allowed)
        
        # Apply pagination
        total = len(domains)
        paginated_domains = domains[offset:offset + limit]
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(paginated_domains)} domains",
            data={
                "domains": paginated_domains,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=StandardResponse)
async def add_domain(
    domain: DomainCreate,
    auth_data: dict = Depends(require_permissions(["domain_manage"]))
):
    """
    Add new domain
    
    Add a new domain to the allowed/blocked list.
    """
    try:
        success = await database_manager.add_domain(
            domain=domain.domain,
            is_allowed=domain.is_allowed
        )
        
        if success:
            return StandardResponse(
                success=True,
                message=f"Domain {domain.domain} added successfully",
                data={"domain": domain.domain, "is_allowed": domain.is_allowed}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to add domain")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{domain_name}", response_model=StandardResponse)
async def update_domain(
    domain_name: str,
    domain_update: DomainUpdate,
    auth_data: dict = Depends(require_permissions(["domain_manage"]))
):
    """
    Update domain settings
    
    Update settings for an existing domain.
    """
    try:
        # Get current domain
        domains = await database_manager.get_domains()
        existing_domain = next((d for d in domains if d['domain'] == domain_name), None)
        
        if not existing_domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Update domain
        update_data = domain_update.dict(exclude_unset=True)
        success = await database_manager.add_domain(
            domain=domain_name,
            is_allowed=update_data.get('is_allowed', existing_domain['is_allowed'])
        )
        
        if success:
            return StandardResponse(
                success=True,
                message=f"Domain {domain_name} updated successfully",
                data={"domain": domain_name, "updates": update_data}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update domain")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{domain_name}", response_model=StandardResponse)
async def delete_domain(
    domain_name: str,
    auth_data: dict = Depends(require_permissions(["domain_manage"]))
):
    """
    Delete domain
    
    Remove a domain from the system.
    """
    try:
        # For now, we'll mark it as not allowed instead of deleting
        success = await database_manager.add_domain(
            domain=domain_name,
            is_allowed=False
        )
        
        if success:
            return StandardResponse(
                success=True,
                message=f"Domain {domain_name} deleted successfully",
                data={"domain": domain_name}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to delete domain")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain_name}", response_model=StandardResponse)
async def get_domain(
    domain_name: str,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get specific domain
    
    Retrieve details for a specific domain.
    """
    try:
        domains = await database_manager.get_domains()
        domain = next((d for d in domains if d['domain'] == domain_name), None)
        
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        return StandardResponse(
            success=True,
            message="Domain retrieved successfully",
            data=domain
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check", response_model=StandardResponse)
async def check_domain(
    domain: str,
    auth_data: dict = Depends(verify_api_key)
):
    """
    Check if domain is allowed
    
    Check if a domain is allowed for auto-reply functionality.
    """
    try:
        domains = await database_manager.get_domains(is_allowed=True)
        allowed_domains = {d['domain'] for d in domains}
        
        is_allowed = domain.lower() in allowed_domains
        
        return StandardResponse(
            success=True,
            message=f"Domain {domain} is {'allowed' if is_allowed else 'not allowed'}",
            data={
                "domain": domain,
                "is_allowed": is_allowed,
                "auto_reply_enabled": is_allowed
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-add", response_model=StandardResponse)
async def bulk_add_domains(
    domains: List[str],
    is_allowed: bool = True,
    auth_data: dict = Depends(require_permissions(["domain_manage"]))
):
    """
    Bulk add domains
    
    Add multiple domains at once.
    """
    try:
        results = []
        errors = []
        
        for domain in domains:
            try:
                success = await database_manager.add_domain(
                    domain=domain.lower().strip(),
                    is_allowed=is_allowed
                )
                
                if success:
                    results.append({"domain": domain, "status": "added"})
                else:
                    errors.append({"domain": domain, "error": "Failed to add"})
                    
            except Exception as e:
                errors.append({"domain": domain, "error": str(e)})
        
        return StandardResponse(
            success=len(errors) == 0,
            message=f"Added {len(results)} domains, {len(errors)} errors",
            data={
                "added": results,
                "errors": errors,
                "total_requested": len(domains)
            }
        )
        
    except Exception as e:
        logger.error(f"Error bulk adding domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StandardResponse)
async def get_domain_stats(
    auth_data: dict = Depends(verify_api_key)
):
    """
    Get domain statistics
    
    Retrieve statistics about domains and their usage.
    """
    try:
        all_domains = await database_manager.get_domains()
        
        allowed_count = len([d for d in all_domains if d.get('is_allowed', False)])
        blocked_count = len([d for d in all_domains if not d.get('is_allowed', True)])
        
        # Get domain usage from email logs (last 30 days)
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        logs = await database_manager.get_email_logs(
            limit=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Count emails by domain
        domain_usage = {}
        for log in logs:
            sender = log.get('sender', '')
            if '@' in sender:
                domain = sender.split('@')[-1].lower()
                domain_usage[domain] = domain_usage.get(domain, 0) + 1
        
        # Top domains by usage
        top_domains = sorted(domain_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats = {
            "total_domains": len(all_domains),
            "allowed_domains": allowed_count,
            "blocked_domains": blocked_count,
            "top_domains_30_days": [{"domain": d, "email_count": c} for d, c in top_domains],
            "period": "30_days"
        }
        
        return StandardResponse(
            success=True,
            message="Domain statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting domain stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
