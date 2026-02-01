"""Student Packages API - Decision tracking for package purchases."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from core.audit import AuditLogger
from core.dependencies import get_current_student_user, get_current_user
from core.rate_limiting import limiter
from core.transactions import atomic_operation
from database import get_db
from models import Booking, StudentPackage, TutorPricingOption, TutorProfile, User
from modules.bookings.domain.status import SessionState
from modules.packages.services.expiration_service import PackageExpirationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/packages", tags=["packages"])


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


class PackagePurchaseResponse(BaseModel):
    """Package purchase response with optional warning for active sessions."""

    package: PackageResponse
    warning: str | None = None
    active_booking_id: int | None = None


@router.post("", response_model=PackagePurchaseResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def purchase_package(
    request: Request,
    purchase_data: PackagePurchaseRequest,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """
    Purchase a package from a tutor.

    **Important Note on Package Application:**
    Packages only apply to FUTURE bookings. If a student purchases a package
    while they have an active session in progress, that session will still be
    charged as pay-per-session. The package credits will be available for
    subsequent bookings only.

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

    # Check for active sessions - packages only apply to future bookings
    # This is informational (warning), not a blocker
    active_session = (
        db.query(Booking)
        .filter(
            Booking.student_id == current_user.id,
            Booking.session_state == SessionState.ACTIVE.value,
            Booking.deleted_at.is_(None),
        )
        .first()
    )

    active_session_warning = None
    active_booking_id = None
    if active_session:
        active_session_warning = (
            "You have an active session in progress. This package will only apply to "
            "future bookings, not your current session which will be charged separately."
        )
        active_booking_id = active_session.id
        logger.info(
            f"Student {current_user.email} purchasing package during active session "
            f"(booking ID: {active_session.id}). Package will apply to future bookings only."
        )

    # Calculate expiration date (if pricing option has validity)
    expires_at = None
    if pricing_option.validity_days:
        expires_at = datetime.utcnow() + timedelta(days=pricing_option.validity_days)

    try:
        # Use atomic transaction to ensure package + audit logs are created together
        # Prevents orphaned packages without proper audit trail
        with atomic_operation(db):
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
            db.flush()  # Get package.id for audit logs

            # Track the purchase decision in audit log (atomically with package)
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

            # Also log general audit entry (atomically with package)
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
            # atomic_operation commits all records together

        db.refresh(package)

        logger.info(
            f"Package purchased: ID {package.id} by student {current_user.email} "
            f"for tutor {tutor.id} - Financial decision tracked"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing package: {e}")
        raise HTTPException(status_code=500, detail="Failed to purchase package")

    return PackagePurchaseResponse(
        package=PackageResponse.model_validate(package),
        warning=active_session_warning,
        active_booking_id=active_booking_id,
    )


@router.get("", response_model=list[PackageResponse])
@limiter.limit("100/minute")
async def list_my_packages(
    request: Request,
    status_filter: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's packages."""
    # Mark expired packages before listing
    try:
        PackageExpirationService.mark_expired_packages(db)
    except Exception as e:
        logger.warning(f"Failed to mark expired packages: {e}")

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

    Uses atomic SQL operations to prevent race conditions where two
    concurrent requests could consume the same credit.

    Rolling Expiry: If the pricing option has extend_on_use=True, the package
    expiration date is extended by validity_days from the current time on each use.
    """
    # First, acquire a lock on the package row to prevent race conditions
    # Also eagerly load the pricing_option to check extend_on_use
    package = (
        db.query(StudentPackage)
        .options(joinedload(StudentPackage.pricing_option))
        .filter(
            StudentPackage.id == package_id,
            StudentPackage.student_id == current_user.id,
        )
        .with_for_update(nowait=False)
        .first()
    )

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Check package validity (includes expiration check)
    is_valid, error_message = PackageExpirationService.check_package_validity(package)
    if not is_valid:
        # If expired, mark it atomically and commit
        if "expired" in error_message.lower() and package.status == "active":
            db.execute(
                update(StudentPackage)
                .where(
                    StudentPackage.id == package_id,
                    StudentPackage.status == "active",
                )
                .values(
                    status="expired",
                    updated_at=datetime.now(UTC),
                )
            )
            db.commit()
        raise HTTPException(status_code=400, detail=error_message)

    try:
        old_remaining = package.sessions_remaining
        old_expires_at = package.expires_at

        # Prepare update values
        update_values = {
            "sessions_remaining": StudentPackage.sessions_remaining - 1,
            "sessions_used": StudentPackage.sessions_used + 1,
            "updated_at": datetime.now(UTC),
        }

        # Rolling expiry: extend validity on each use if enabled
        pricing_option = package.pricing_option
        new_expires_at = None
        if (
            pricing_option
            and pricing_option.extend_on_use
            and pricing_option.validity_days
        ):
            new_expires_at = datetime.now(UTC) + timedelta(days=pricing_option.validity_days)
            # Only extend if the new date is later than current expiration
            if package.expires_at is None or new_expires_at > package.expires_at:
                update_values["expires_at"] = new_expires_at
                # Reset expiry warning flag since validity was extended
                update_values["expiry_warning_sent"] = False
                logger.info(
                    f"Rolling expiry: extending package {package_id} from "
                    f"{package.expires_at} to {new_expires_at}"
                )

        # Atomic credit deduction with validation guard
        # This prevents race conditions where two requests could consume the same credit
        result = db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.student_id == current_user.id,
                StudentPackage.sessions_remaining > 0,
                StudentPackage.status == "active",
            )
            .values(**update_values)
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=400,
                detail="No credits available or package is not active",
            )

        # NOTE: Do NOT set "exhausted" status here!
        # The status should only be updated after all operations succeed,
        # just before commit. This ensures the package status is not
        # prematurely set to "exhausted" if subsequent operations fail.
        # See the status update below, just before commit.

        # Refresh to get updated values for audit logging
        db.refresh(package)

        # Track credit usage decision
        audit_new_data = {
            "sessions_remaining": package.sessions_remaining,
            "sessions_used": package.sessions_used,
            "status": package.status,
            "decision": "used_credit_for_booking",
            "used_at": datetime.now(UTC).isoformat(),
        }
        if new_expires_at and "expires_at" in update_values:
            audit_new_data["expires_at_extended_to"] = new_expires_at.isoformat()
            audit_new_data["rolling_expiry_applied"] = True

        AuditLogger.log_action(
            db=db,
            table_name="student_packages",
            record_id=package_id,
            action="UPDATE",
            old_data={
                "sessions_remaining": old_remaining,
                "expires_at": old_expires_at.isoformat() if old_expires_at else None,
            },
            new_data=audit_new_data,
            changed_by=current_user.id,
            ip_address=request.client.host if request.client else None,
        )

        # Now that all operations are complete, safely update package status
        # to "exhausted" if sessions_remaining is 0.
        # This is done just before commit to ensure the status is not set
        # prematurely if earlier operations fail.
        db.execute(
            update(StudentPackage)
            .where(
                StudentPackage.id == package_id,
                StudentPackage.sessions_remaining == 0,
                StudentPackage.status == "active",
            )
            .values(
                status="exhausted",
                updated_at=datetime.now(UTC),
            )
        )

        db.commit()
        db.refresh(package)

        logger.info(
            f"Credit used from package {package_id} by student {current_user.email} "
            f"- {package.sessions_remaining} credits remaining"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error using package credit: {e}")
        raise HTTPException(status_code=500, detail="Failed to use credit")

    return package
