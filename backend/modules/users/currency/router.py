"""User currency management API."""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from core.rate_limiting import limiter

from sqlalchemy.orm import Session

from core.currency import CurrencyOption, load_supported_currencies
from core.dependencies import get_current_user
from database import get_db
from models import User
from schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/currency", tags=["user-currency"])


class CurrencyUpdateRequest(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)


@router.get("/options", response_model=list[CurrencyOption])
@limiter.limit("30/minute")
def list_currency_options(request: Request, db: Session = Depends(get_db)) -> list[CurrencyOption]:
    """Return the list of supported currencies."""
    currencies = load_supported_currencies(db)
    logger.debug("Loaded %d currency options", len(currencies))
    return currencies


@router.patch("", response_model=UserResponse)
@limiter.limit("20/minute")
def update_currency(
    request: Request,
    payload: CurrencyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's preferred currency."""
    currencies = load_supported_currencies(db)
    allowed_codes = {item.code.upper() for item in currencies}

    currency_code = payload.currency.upper()
    if currency_code not in allowed_codes:
        logger.warning("Attempt to set unsupported currency: %s", currency_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported currency code",
        )

    current_user.currency = currency_code

    # Update timestamp in application code (no DB triggers)
    from datetime import datetime

    current_user.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(current_user)

    logger.info("Updated currency for user %s to %s", current_user.email, currency_code)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        avatar_url=None,
        currency=current_user.currency,
        timezone=current_user.timezone,
    )
