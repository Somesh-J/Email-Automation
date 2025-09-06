"""
Template management routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
import logging
from datetime import datetime

from ..models import (
    StandardResponse, EmailTemplate, EmailTemplateCreate, 
    EmailTemplateUpdate, TemplateListResponse
)
from core.security import verify_api_key, require_permissions
from core.database import get_db, EmailTemplateDB

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    active_only: bool = True,
    auth_data: dict = Depends(verify_api_key),
    db=Depends(get_db)
):
    """
    List email templates
    
    Retrieve all email templates with optional filtering.
    """
    try:
        query = db.query(EmailTemplateDB)
        
        if active_only:
            query = query.filter(EmailTemplateDB.is_active == True)
        
        if category:
            query = query.filter(EmailTemplateDB.category == category)
        
        total = query.count()
        templates = query.offset(skip).limit(limit).all()
        
        template_list = []
        for template in templates:
            template_list.append(EmailTemplate(
                id=template.id,
                name=template.name,
                subject=template.subject,
                body=template.body,
                category=template.category,
                variables=template.variables or [],
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            ))
        
        return TemplateListResponse(
            success=True,
            message=f"Retrieved {len(template_list)} templates",
            data=template_list,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_id}", response_model=StandardResponse)
async def get_template(
    template_id: int,
    auth_data: dict = Depends(verify_api_key),
    db=Depends(get_db)
):
    """
    Get a specific template
    
    Retrieve details of a specific email template.
    """
    try:
        template = db.query(EmailTemplateDB).filter(EmailTemplateDB.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_data = EmailTemplate(
            id=template.id,
            name=template.name,
            subject=template.subject,
            body=template.body,
            category=template.category,
            variables=template.variables or [],
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
        return StandardResponse(
            success=True,
            message="Template retrieved successfully",
            data=template_data.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=StandardResponse)
async def create_template(
    template: EmailTemplateCreate,
    auth_data: dict = Depends(require_permissions(["templates_manage"])),
    db=Depends(get_db)
):
    """
    Create a new template
    
    Create a new email template.
    """
    try:
        # Check if template name already exists
        existing = db.query(EmailTemplateDB).filter(EmailTemplateDB.name == template.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Template name already exists")
        
        db_template = EmailTemplateDB(
            name=template.name,
            subject=template.subject,
            body=template.body,
            category=template.category,
            variables=template.variables,
            is_active=template.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        created_template = EmailTemplate(
            id=db_template.id,
            name=db_template.name,
            subject=db_template.subject,
            body=db_template.body,
            category=db_template.category,
            variables=db_template.variables or [],
            is_active=db_template.is_active,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )
        
        return StandardResponse(
            success=True,
            message="Template created successfully",
            data=created_template.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{template_id}", response_model=StandardResponse)
async def update_template(
    template_id: int,
    template: EmailTemplateUpdate,
    auth_data: dict = Depends(require_permissions(["templates_manage"])),
    db=Depends(get_db)
):
    """
    Update a template
    
    Update an existing email template.
    """
    try:
        db_template = db.query(EmailTemplateDB).filter(EmailTemplateDB.id == template_id).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check if new name conflicts with existing template
        if template.name and template.name != db_template.name:
            existing = db.query(EmailTemplateDB).filter(EmailTemplateDB.name == template.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Template name already exists")
        
        # Update fields
        update_data = template.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db_template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_template)
        
        updated_template = EmailTemplate(
            id=db_template.id,
            name=db_template.name,
            subject=db_template.subject,
            body=db_template.body,
            category=db_template.category,
            variables=db_template.variables or [],
            is_active=db_template.is_active,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )
        
        return StandardResponse(
            success=True,
            message="Template updated successfully",
            data=updated_template.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{template_id}", response_model=StandardResponse)
async def delete_template(
    template_id: int,
    auth_data: dict = Depends(require_permissions(["templates_manage"])),
    db=Depends(get_db)
):
    """
    Delete a template
    
    Delete an email template.
    """
    try:
        db_template = db.query(EmailTemplateDB).filter(EmailTemplateDB.id == template_id).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        db.delete(db_template)
        db.commit()
        
        return StandardResponse(
            success=True,
            message="Template deleted successfully",
            data={"template_id": template_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/list", response_model=StandardResponse)
async def list_categories(
    auth_data: dict = Depends(verify_api_key),
    db=Depends(get_db)
):
    """
    List template categories
    
    Get all unique template categories.
    """
    try:
        categories = db.query(EmailTemplateDB.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return StandardResponse(
            success=True,
            message="Categories retrieved successfully",
            data={"categories": category_list}
        )
        
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/duplicate", response_model=StandardResponse)
async def duplicate_template(
    template_id: int,
    new_name: str,
    auth_data: dict = Depends(require_permissions(["templates_manage"])),
    db=Depends(get_db)
):
    """
    Duplicate a template
    
    Create a copy of an existing template with a new name.
    """
    try:
        original = db.query(EmailTemplateDB).filter(EmailTemplateDB.id == template_id).first()
        
        if not original:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check if new name already exists
        existing = db.query(EmailTemplateDB).filter(EmailTemplateDB.name == new_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Template name already exists")
        
        duplicate = EmailTemplateDB(
            name=new_name,
            subject=original.subject,
            body=original.body,
            category=original.category,
            variables=original.variables,
            is_active=False,  # New templates start as inactive
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        
        new_template = EmailTemplate(
            id=duplicate.id,
            name=duplicate.name,
            subject=duplicate.subject,
            body=duplicate.body,
            category=duplicate.category,
            variables=duplicate.variables or [],
            is_active=duplicate.is_active,
            created_at=duplicate.created_at,
            updated_at=duplicate.updated_at
        )
        
        return StandardResponse(
            success=True,
            message="Template duplicated successfully",
            data=new_template.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating template {template_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/test", response_model=StandardResponse)
async def test_template(
    template_id: int,
    test_variables: dict = {},
    auth_data: dict = Depends(verify_api_key),
    db=Depends(get_db)
):
    """
    Test a template
    
    Test template rendering with provided variables.
    """
    try:
        template = db.query(EmailTemplateDB).filter(EmailTemplateDB.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Simple variable substitution (in production, use a proper template engine)
        rendered_subject = template.subject
        rendered_body = template.body
        
        for key, value in test_variables.items():
            placeholder = f"{{{key}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
            rendered_body = rendered_body.replace(placeholder, str(value))
        
        return StandardResponse(
            success=True,
            message="Template rendered successfully",
            data={
                "original_subject": template.subject,
                "original_body": template.body,
                "rendered_subject": rendered_subject,
                "rendered_body": rendered_body,
                "variables_used": test_variables
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import", response_model=StandardResponse)
async def import_templates(
    templates: List[EmailTemplateCreate],
    background_tasks: BackgroundTasks,
    auth_data: dict = Depends(require_permissions(["templates_manage"])),
    db=Depends(get_db)
):
    """
    Import multiple templates
    
    Import multiple email templates at once.
    """
    try:
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for template in templates:
            try:
                # Check if template name already exists
                existing = db.query(EmailTemplateDB).filter(EmailTemplateDB.name == template.name).first()
                if existing:
                    skipped_count += 1
                    continue
                
                db_template = EmailTemplateDB(
                    name=template.name,
                    subject=template.subject,
                    body=template.body,
                    category=template.category,
                    variables=template.variables,
                    is_active=template.is_active,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(db_template)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing template '{template.name}': {str(e)}")
        
        db.commit()
        
        return StandardResponse(
            success=True,
            message=f"Import completed: {imported_count} imported, {skipped_count} skipped",
            data={
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error(f"Error importing templates: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
