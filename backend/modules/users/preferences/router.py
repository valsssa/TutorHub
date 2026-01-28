"""User preferences API router."""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from models import User
from schemas import UserPreferencesUpdate, UserResponse

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/users/preferences", tags=["user-preferences"])


@router.patch("", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_preferences(
    request: Request,
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user preferences (timezone)."""
    logger.info(f"Updating preferences for user: {current_user.email}")

    if preferences.timezone:
        current_user.timezone = preferences.timezone
        logger.debug(f"Updated timezone to: {preferences.timezone}")

        # Update timestamp in application code (no DB triggers)
        from datetime import datetime

        current_user.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        avatar_url=None,  # Will be fetched separately if needed
        currency=current_user.currency,
        timezone=current_user.timezone,
    )
