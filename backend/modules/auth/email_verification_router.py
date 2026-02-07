"""
Email Verification Router

Handles email verification flow:
- Send verification email
- Verify email token
- Resend verification email
"""

import logging
import secrets
from datetime import datetime, timedelta

from core.datetime_utils import utc_now

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from core.dependencies import DatabaseSession
from core.email_service import email_service
from core.utils import StringUtils
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# In-memory token storage (use Redis in production)
_verification_tokens: dict[str, dict] = {}


# ============================================================================
# Schemas
# ============================================================================


class EmailVerificationRequest(BaseModel):
    """Request to send verification email."""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Verify email with token."""
    token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/email/send-verification",
    response_model=MessageResponse,
    summary="Send verification email",
    description="""
**Send email verification link**

Sends a verification email to the user. For security, we always return success
even if the email doesn't exist or is already verified.
    """,
)
async def send_verification_email(
    request: EmailVerificationRequest,
    db: DatabaseSession,
) -> MessageResponse:
    """Send email verification."""

    email = StringUtils.normalize_email(request.email)

    # Find user - exclude soft-deleted users
    user = db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None),
    ).first()

    if user and user.is_active and not user.is_verified:
        # Generate verification token
        token = secrets.token_urlsafe(32)
        _verification_tokens[token] = {
            "user_id": user.id,
            "email": email,
            "created_at": utc_now(),
        }

        # Clean up old tokens
        cutoff = utc_now() - timedelta(hours=48)
        for t, data in list(_verification_tokens.items()):
            if data["created_at"] < cutoff:
                del _verification_tokens[t]

        # Send verification email
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
        email_service.send_email_verification(
            email=email,
            name=name,
            verification_token=token,
        )

        logger.info(f"Verification email sent to {email}")

    # Always return success for security
    return MessageResponse(
        message="If an unverified account exists with this email, you will receive a verification link."
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
    description="Verify email address using the token from the verification email.",
)
async def verify_email(
    request: EmailVerificationConfirm,
    db: DatabaseSession,
) -> MessageResponse:
    """Verify email with token."""

    token_data = _verification_tokens.get(request.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Check if expired (24 hours)
    if utc_now() - token_data["created_at"] > timedelta(hours=24):
        del _verification_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    # Get user - exclude soft-deleted users
    user = db.query(User).filter(
        User.id == token_data["user_id"],
        User.deleted_at.is_(None),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    if user.is_verified:
        # Consume token even if already verified
        del _verification_tokens[request.token]
        return MessageResponse(message="Email has already been verified")

    # Mark email as verified
    now = utc_now()
    user.is_verified = True
    user.updated_at = now
    db.commit()

    # Consume token
    del _verification_tokens[request.token]

    logger.info(f"Email verified for user {user.id}")

    return MessageResponse(message="Email verified successfully")


@router.post(
    "/email/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Resend the email verification link.",
)
async def resend_verification_email(
    request: EmailVerificationRequest,
    db: DatabaseSession,
) -> MessageResponse:
    """Resend email verification."""
    # Reuse the send_verification_email logic
    return await send_verification_email(request, db)
