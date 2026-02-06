"""
Password Reset Router

Handles password reset flow:
- Request reset (sends email)
- Verify token
- Reset password

Tokens are stored in Redis via CachePort for multi-instance safety.
"""

import json
import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from core.dependencies import CacheDep, DatabaseSession
from core.email_service import email_service
from core.security import PasswordHasher
from core.utils import StringUtils
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Redis key prefix for password reset tokens
_RESET_TOKEN_PREFIX = "password_reset:"
_RESET_TOKEN_TTL = 3600  # 1 hour in seconds


# ============================================================================
# Schemas
# ============================================================================


class PasswordResetRequest(BaseModel):
    """Request password reset."""
    email: EmailStr


class PasswordResetVerify(BaseModel):
    """Verify reset token."""
    token: str


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with new password."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/password/reset-request",
    response_model=MessageResponse,
    summary="Request password reset",
    description="""
**Request a password reset email**

If the email exists, a reset link will be sent. For security, we always return success
even if the email doesn't exist.
    """,
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: DatabaseSession,
    cache: CacheDep,
) -> MessageResponse:
    """Request password reset email."""

    email = StringUtils.normalize_email(request.email)

    # Find user (don't reveal if exists) - exclude soft-deleted users
    user = db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None),
    ).first()

    if user and user.is_active:
        # Generate reset token
        token = secrets.token_urlsafe(32)
        token_data = {
            "user_id": user.id,
            "email": email,
            "created_at": datetime.now(UTC).isoformat(),
        }

        # Store in Redis with 1-hour TTL (auto-expires, no cleanup needed)
        await cache.set(
            f"{_RESET_TOKEN_PREFIX}{token}",
            json.dumps(token_data),
            ttl_seconds=_RESET_TOKEN_TTL,
        )

        # Send email
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
        email_service.send_password_reset(
            email=email,
            name=name,
            reset_token=token,
            expires_in_hours=1,
        )

        logger.info(f"Password reset requested for {email}")

    # Always return success for security
    return MessageResponse(
        message="If an account exists with this email, you will receive a password reset link."
    )


@router.post(
    "/password/verify-token",
    response_model=MessageResponse,
    summary="Verify reset token",
    description="Check if a password reset token is valid.",
)
async def verify_reset_token(
    request: PasswordResetVerify,
    cache: CacheDep,
) -> MessageResponse:
    """Verify password reset token."""

    raw = await cache.get(f"{_RESET_TOKEN_PREFIX}{request.token}")

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return MessageResponse(message="Token is valid")


@router.post(
    "/password/reset-confirm",
    response_model=MessageResponse,
    summary="Reset password",
    description="Set a new password using the reset token.",
)
async def reset_password(
    request: PasswordResetConfirm,
    db: DatabaseSession,
    cache: CacheDep,
) -> MessageResponse:
    """Reset password with token."""

    cache_key = f"{_RESET_TOKEN_PREFIX}{request.token}"
    raw = await cache.get(cache_key)

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    token_data = json.loads(raw)

    # Get user - exclude soft-deleted users
    user = db.query(User).filter(
        User.id == token_data["user_id"],
        User.deleted_at.is_(None),
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update password and track change time for token invalidation
    now = datetime.now(UTC)
    user.hashed_password = PasswordHasher.hash(request.new_password)
    user.password_changed_at = now
    user.updated_at = now
    db.commit()

    # Consume token (delete from Redis)
    await cache.delete(cache_key)

    logger.info(f"Password reset completed for user {user.id}")

    return MessageResponse(message="Password has been reset successfully")
