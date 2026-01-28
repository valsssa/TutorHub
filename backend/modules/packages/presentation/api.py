"""Student Packages API - Decision tracking for package purchases."""

import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.audit import AuditLogger
from core.dependencies import get_current_student_user, get_current_user
from database import get_db
from models import StudentPackage, TutorPricingOption, TutorProfile, User

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/packages", tags=["packages"])


# Schemas
class PackagePurchaseRequest(BaseModel):
    """Request to purchase a package."""

    tutor_profile_id: int
    pricing_option_id: int
    payment_intent_id: str | None = None
    agreed_terms: str | None = Field(None, description="User agreement to package terms")


class PackageResponse(BaseModel):
    """Package purchase response."""

    id: int
    student_id: int
    tutor_profile_id: int
    pricing_option_id: int
    sessions_purchased: int
    sessions_remaining: int
    sessions_used: int
    purchase_price: Decimal
    purchased_at: datetime
    expires_at: datetime | None
    status: str
    payment_intent_id: str | None

    class Config:
        from_attributes = True


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def purchase_package(
    request: Request,
    purchase_data: PackagePurchaseRequest,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """
    Purchase a package from a tutor.

    **Decision Tracking Philosophy:**
    This captures the critical moment when a student DECIDES to commit
    financially to sessions with a specific tutor. We track:
    - WHO made the purchase
    - WHAT they purchased (tutor, package, price)
    - WHEN they purchased it
    - WHY (implicitly: chose this tutor's offering)
    - Agreement terms they consented to
    """
    # Verify tutor and pricing option exist
    tutor = (
        db.query(TutorProfile)
        .filter(
            TutorProfile.id == purchase_data.tutor_profile_id,
            TutorProfile.is_approved.is_(True),
        )
        .first()
    )
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found or not approved")

    pricing_option = (
        db.query(TutorPricingOption).filter(TutorPricingOption.id == purchase_data.pricing_option_id).first()
    )
    if not pricing_option:
        raise HTTPException(status_code=404, detail="Pricing option not found")

    # Verify pricing option belongs to tutor
    if pricing_option.tutor_profile_id != purchase_data.tutor_profile_id:
        raise HTTPException(status_code=400, detail="Pricing option does not belong to this tutor")

    # Calculate expiration date (if pricing option has validity)
    expires_at = None
    # TODO: Add validity_days to pricing options if needed
    # if pricing_option.validity_days:
    #     expires_at = datetime.utcnow() + timedelta(days=pricing_option.validity_days)

    try:
        # Create package purchase record
        package = StudentPackage(
            student_id=current_user.id,
            tutor_profile_id=purchase_data.tutor_profile_id,
            pricing_option_id=purchase_data.pricing_option_id,
            sessions_purchased=1,  # Default to 1 session per purchase
            sessions_remaining=1,
            sessions_used=0,
            purchase_price=pricing_option.price,
            purchased_at=datetime.utcnow(),
            expires_at=expires_at,
            status="active",
            payment_intent_id=purchase_data.payment_intent_id,
        )

        db.add(package)
        db.flush()

        # Track the purchase decision in audit log
        AuditLogger.log_payment_decision(
            db=db,
            package_id=package.id,
            user_id=current_user.id,
            amount=float(pricing_option.price),
            currency=tutor.currency or "USD",
            payment_intent_id=purchase_data.payment_intent_id,
            status="completed",
            ip_address=request.client.host if request.client else None,
        )

        # Also log general audit entry
        AuditLogger.log_action(
            db=db,
            table_name="student_packages",
            record_id=package.id,
            action="INSERT",
            new_data={
                "student_id": current_user.id,
                "tutor_profile_id": purchase_data.tutor_profile_id,
                "pricing_option_id": purchase_data.pricing_option_id,
                "purchase_price": float(pricing_option.price),
                "agreed_terms": purchase_data.agreed_terms,
                "purchased_at": datetime.utcnow().isoformat(),
                "decision": "student_purchased_package",
            },
            changed_by=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        db.commit()
        db.refresh(package)

        logger.info(
            f"Package purchased: ID {package.id} by student {current_user.email} "
            f"for tutor {tutor.id} - Financial decision tracked"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error purchasing package: {e}")
        raise HTTPException(status_code=500, detail="Failed to purchase package")

    return package


@router.get("", response_model=list[PackageResponse])
@limiter.limit("100/minute")
async def list_my_packages(
    request: Request,
    status_filter: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's packages."""
    query = db.query(StudentPackage).filter(StudentPackage.student_id == current_user.id)

    if status_filter:
        query = query.filter(StudentPackage.status == status_filter)

    packages = query.order_by(StudentPackage.purchased_at.desc()).all()
    return packages


@router.patch("/{package_id}/use-credit", response_model=PackageResponse)
@limiter.limit("50/minute")
async def use_package_credit(
    request: Request,
    package_id: int,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """
    Use one credit from a package when booking a session.

    Decision tracking: Records when student DECIDES to use a credit
    instead of paying per-session.
    """
    package = (
        db.query(StudentPackage)
        .filter(
            StudentPackage.id == package_id,
            StudentPackage.student_id == current_user.id,
        )
        .first()
    )

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    if package.status != "active":
        raise HTTPException(status_code=400, detail=f"Package is {package.status}, cannot use credits")

    if package.sessions_remaining <= 0:
        raise HTTPException(status_code=400, detail="No credits remaining in package")

    # Check expiration
    if package.expires_at and package.expires_at < datetime.utcnow():
        package.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Package has expired")

    try:
        old_remaining = package.sessions_remaining

        # Deduct credit
        package.sessions_remaining -= 1
        package.sessions_used += 1

        # Auto-update status if exhausted
        if package.sessions_remaining == 0:
            package.status = "exhausted"

        # Update timestamp in application code (no DB triggers)
        package.updated_at = datetime.now()

        # Track credit usage decision
        AuditLogger.log_action(
            db=db,
            table_name="student_packages",
            record_id=package_id,
            action="UPDATE",
            old_data={"sessions_remaining": old_remaining},
            new_data={
                "sessions_remaining": package.sessions_remaining,
                "sessions_used": package.sessions_used,
                "status": package.status,
                "decision": "used_credit_for_booking",
                "used_at": datetime.utcnow().isoformat(),
            },
            changed_by=current_user.id,
            ip_address=request.client.host if request.client else None,
        )

        db.commit()
        db.refresh(package)

        logger.info(
            f"Credit used from package {package_id} by student {current_user.email} "
            f"- {package.sessions_remaining} credits remaining"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error using package credit: {e}")
        raise HTTPException(status_code=500, detail="Failed to use credit")

    return package
