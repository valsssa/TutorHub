"""User profiles API routes."""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.sanitization import sanitize_text_input
from database import get_db
from models import User, UserProfile
from schemas import UserProfileResponse, UserProfileUpdate

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/profile", tags=["profiles"])


@router.get("/me", response_model=UserProfileResponse)
@limiter.limit("60/minute")
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's profile."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            # Create empty profile
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info(f"Created new profile for user {current_user.email}")
        return profile
    except Exception as e:
        logger.error(f"Error retrieving profile for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.put("/me", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def update_my_profile(
    request: Request,
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)

        # Update fields with sanitization
        update_data = profile_data.model_dump(exclude_unset=True)

        # Sanitize text fields
        if "first_name" in update_data and update_data["first_name"]:
            update_data["first_name"] = sanitize_text_input(update_data["first_name"], max_length=100)

        if "last_name" in update_data and update_data["last_name"]:
            update_data["last_name"] = sanitize_text_input(update_data["last_name"], max_length=100)

        if "bio" in update_data and update_data["bio"]:
            update_data["bio"] = sanitize_text_input(update_data["bio"], max_length=1000)

        # Apply updates to profile
        # NOTE: first_name/last_name removed from UserProfile in Phase 1.2 - names now stored in users table
        for field, value in update_data.items():
            setattr(profile, field, value)

        # Update timestamp in application code (no DB triggers)
        from datetime import datetime

        profile.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(profile)

        logger.info(f"User {current_user.email} updated profile: {list(update_data.keys())}")
        return profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")
