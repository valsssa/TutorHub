"""Subjects API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.cache import cache_with_ttl, invalidate_cache
from core.dependencies import get_current_admin_user
from core.sanitization import sanitize_text_input
from database import get_db
from models import Subject, User
from schemas import SubjectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@cache_with_ttl(ttl_seconds=300)  # Cache for 5 minutes
def _get_cached_subjects(db: Session, include_inactive: bool = False) -> List[Subject]:
    """Helper to fetch subjects with caching."""
    query = db.query(Subject)
    if not include_inactive:
        query = query.filter(Subject.is_active.is_(True))
    return query.all()


@router.get("", response_model=List[SubjectResponse])
@limiter.limit("60/minute")
def list_subjects(
    request: Request,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    """List all active subjects. Public endpoint."""
    # Inactive subjects are never shown to public
    return _get_cached_subjects(db, include_inactive=False)


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_subject(
    request: Request,
    name: str,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create new subject (admin only)."""
    # Sanitize inputs
    name = sanitize_text_input(name, max_length=100)
    if not name or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Subject name is required")

    description = (
        sanitize_text_input(description, max_length=1000) if description else None
    )

    # Check if subject exists
    existing = db.query(Subject).filter(Subject.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject already exists")

    try:
        subject = Subject(name=name, description=description)
        db.add(subject)
        db.commit()
        db.refresh(subject)

        logger.info(f"Subject created: {name} by admin {current_user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating subject: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subject")

    # Invalidate subjects cache
    invalidate_cache(pattern="_get_cached_subjects")

    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
@limiter.limit("20/minute")
async def update_subject(
    request: Request,
    subject_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update subject (admin only)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Sanitize inputs
    if name is not None:
        name = sanitize_text_input(name, max_length=100)
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Subject name cannot be empty")
        subject.name = name

    if description is not None:
        subject.description = sanitize_text_input(description, max_length=1000)

    if is_active is not None:
        subject.is_active = is_active
    
    # Update timestamp in application code (no DB triggers)
    from datetime import datetime, timezone
    subject.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(subject)
        logger.info(f"Subject updated: {subject_id} by admin {current_user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating subject: {e}")
        raise HTTPException(status_code=500, detail="Failed to update subject")

    # Invalidate subjects cache
    invalidate_cache(pattern="_get_cached_subjects")

    return subject


@router.delete("/{subject_id}")
@limiter.limit("20/minute")
async def delete_subject(
    request: Request,
    subject_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Soft delete subject (admin only) - sets is_active to False."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Soft delete instead of hard delete
    subject.is_active = False
    
    # Update timestamp in application code (no DB triggers)
    from datetime import datetime, timezone
    subject.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        logger.info(f"Subject soft-deleted: {subject_id} by admin {current_user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting subject: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete subject")

    # Invalidate subjects cache
    invalidate_cache(pattern="_get_cached_subjects")

    return {"message": "Subject deleted"}
