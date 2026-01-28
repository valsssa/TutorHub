"""
Password Reset Router

Handles password reset flow:
- Request reset (sends email)
- Verify token
- Reset password
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import DatabaseSession
from core.email_service import email_service
from core.security import PasswordHasher
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)

# In-memory token storage (use Redis in production)
_reset_tokens: dict[str, dict] = {}


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
) -> MessageResponse:
    """Request password reset email."""

    email = request.email.lower().strip()

    # Find user (don't reveal if exists)
    user = db.query(User).filter(User.email == email).first()

    if user and user.is_active:
        # Generate reset token
        token = secrets.token_urlsafe(32)
        _reset_tokens[token] = {
            "user_id": user.id,
            "email": email,
            "created_at": datetime.now(UTC),
        }

        # Clean up old tokens
        cutoff = datetime.now(UTC) - timedelta(hours=2)
        for t, data in list(_reset_tokens.items()):
            if data["created_at"] < cutoff:
                del _reset_tokens[t]

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
) -> MessageResponse:
    """Verify password reset token."""

    token_data = _reset_tokens.get(request.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if expired (1 hour)
    if datetime.now(UTC) - token_data["created_at"] > timedelta(hours=1):
        del _reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
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
) -> MessageResponse:
    """Reset password with token."""

    token_data = _reset_tokens.get(request.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if expired
    if datetime.now(UTC) - token_data["created_at"] > timedelta(hours=1):
        del _reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Get user
    user = db.query(User).filter(User.id == token_data["user_id"]).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update password
    user.hashed_password = PasswordHasher.hash(request.new_password)
    user.updated_at = datetime.now(UTC)
    db.commit()

    # Consume token
    del _reset_tokens[request.token]

    logger.info(f"Password reset completed for user {user.id}")

    return MessageResponse(message="Password has been reset successfully")
