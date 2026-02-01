"""Admin API routes."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel
from core.rate_limiting import limiter

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from core.dependencies import get_current_admin_user
from core.pagination import PaginatedResponse, PaginationParams
from core.sanitization import sanitize_text_input
from core.transactions import atomic_operation
from core.utils import StringUtils, paginate
from database import get_db
from models import Booking, Notification, Review, Subject, TutorProfile, User
from modules.users.avatar.schemas import AvatarResponse
from modules.users.avatar.service import AvatarService
from schemas import (
    BookingResponse,
    TutorProfileResponse,
    TutorRejectionRequest,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("audit.avatar")

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=PaginatedResponse[UserResponse])
@limiter.limit("60/minute")
async def list_all_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query(
        "all",
        pattern="^(all|active|inactive)$",
        description="Filter by user status",
    ),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated list of all platform users with filtering.

    ## Business Logic
    - Excludes tutors with unapproved profiles from the results
    - Supports filtering by active/inactive status
    - Results ordered by creation date (newest first)
    - Default page size: 20, maximum: 100

    ## Permissions
    - **Required Role**: Admin only
    - Authentication via JWT in Authorization header
    - Non-admin users receive 403 Forbidden

    ## Query Parameters
    - `page` (int): Page number (min: 1, default: 1)
    - `page_size` (int): Items per page (min: 1, max: 100, default: 20)
    - `status` (str): Filter by status - "all", "active", or "inactive" (default: "all")

    ## Response
    Returns paginated user list with metadata:
    - `items`: Array of UserResponse objects
    - `total`: Total count of matching users
    - `page`: Current page number
    - `page_size`: Items per page
    - `pages`: Total number of pages

    ## Rate Limiting
    - **Limit**: 60 requests per minute per IP
    - Exceeding limit returns 429 Too Many Requests

    ## Error Responses
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: User is not an admin
    - `422 Unprocessable Entity`: Invalid query parameters
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Database or server error

    ## Example Usage
    ```bash
    curl -X GET "http://localhost:8000/api/admin/users?page=1&page_size=20&status=active" \\
         -H "Authorization: Bearer {admin_token}"
    ```
    """
    pagination = PaginationParams(page=page, page_size=page_size)

    # Base query excludes tutors without approved profiles
    query = (
        db.query(User)
        .outerjoin(TutorProfile, User.id == TutorProfile.user_id)
        .filter((User.role != "tutor") | (TutorProfile.id.is_(None)) | (TutorProfile.is_approved.is_(True)))
        .order_by(User.created_at.desc())
    )

    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))

    try:
        result = paginate(query, page=pagination.page, page_size=pagination.page_size)
        logger.info(f"Admin {current_user.email} listed users (page {page})")
        return result
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users") from e


@router.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Update user details including role assignment with automatic profile management.

    ## Business Logic
    - Automatically maintains role-profile consistency:
      * Changing role to 'tutor' creates tutor_profiles record
      * Changing role from 'tutor' archives tutor_profiles record
    - Email addresses are automatically normalized (lowercase, trimmed)
    - Admins cannot change their own role (self-protection)
    - Role changes trigger domain events for audit logging

    ## Permissions
    - **Required Role**: Admin only
    - Cannot modify own admin role
    - Authentication via JWT in Authorization header

    ## Path Parameters
    - `user_id` (int): Target user's unique identifier

    ## Request Body (UserUpdate)
    All fields optional (partial update):
    - `email` (str): New email address (auto-normalized)
    - `role` (str): New role - "student", "tutor", or "admin"
    - `is_active` (bool): Account active status

    ## Response
    Returns updated UserResponse object with all user fields

    ## Audit Trail
    - All role changes create immutable audit log entries
    - Logged details: changed_by, old_role, new_role, timestamp

    ## Rate Limiting
    - **Limit**: 30 requests per minute per IP
    - Prevents bulk unauthorized modifications

    ## Error Responses
    - `400 Bad Request`: Attempting to change own admin role
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: User is not an admin
    - `404 Not Found`: User ID does not exist
    - `422 Unprocessable Entity`: Invalid update data
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Database or server error

    ## Example Usage
    ```bash
    curl -X PUT "http://localhost:8000/api/admin/users/42" \\
         -H "Authorization: Bearer {admin_token}" \\
         -H "Content-Type: application/json" \\
         -d '{"role": "tutor", "is_active": true}'
    ```
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from modifying their own account in restricted ways
    if user.id == current_user.id:
        if user_update.is_active is False:
            logger.warning(f"Admin {current_user.email} attempted to deactivate their own account")
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if user_update.role and user_update.role != user.role:
            logger.warning(f"Admin {current_user.email} attempted to change their own role")
            raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Prevent removing the last active admin
    if user.role == "admin" and user.is_active:
        is_losing_admin_status = (
            (user_update.role is not None and user_update.role != "admin")
            or (user_update.is_active is False)
        )
        if is_losing_admin_status:
            other_active_admins = (
                db.query(User)
                .filter(
                    User.role == "admin",
                    User.is_active.is_(True),
                    User.deleted_at.is_(None),
                    User.id != user.id,
                )
                .count()
            )
            if other_active_admins == 0:
                logger.warning(
                    f"Admin {current_user.email} attempted to remove last admin {user.email}"
                )
                raise HTTPException(
                    status_code=400, detail="Cannot remove the last active admin"
                )

    try:
        # Track original role for change detection
        old_role = user.role

        # Update fields with validation
        update_data = user_update.model_dump(exclude_unset=True)

        # Sanitize email if provided
        if "email" in update_data and update_data["email"]:
            update_data["email"] = StringUtils.normalize_email(update_data["email"])

        # Use atomic transaction to ensure user update + profile creation
        # happen together (prevents orphaned profiles on partial failure)
        with atomic_operation(db):
            for field, value in update_data.items():
                setattr(user, field, value)

            # Update timestamp in application code (no DB triggers)
            user.updated_at = datetime.now(UTC)

            # Handle role change side effects (maintain role-profile consistency)
            # Profile creation/archival happens atomically with user role update
            if "role" in update_data and update_data["role"] != old_role:
                from modules.users.domain.events import UserRoleChanged
                from modules.users.domain.handlers import RoleChangeEventHandler

                event = UserRoleChanged(
                    user_id=user.id,
                    old_role=old_role,
                    new_role=update_data["role"],
                    changed_by=current_user.id,
                )

                handler = RoleChangeEventHandler()
                handler.handle(db, event)
            # atomic_operation commits all changes together

        db.refresh(user)

        logger.info(f"Admin {current_user.email} updated user {user_id}: {list(update_data.keys())}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.patch("/users/{user_id}/avatar", response_model=AvatarResponse)
@limiter.limit("10/minute")
async def admin_update_user_avatar(
    request: Request,
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> AvatarResponse:
    """
    Upload or replace a user's avatar image (admin privilege).

    ## Business Logic
    - Admin can update any user's avatar
    - Replaces existing avatar if one exists
    - Validates image format and size
    - Stores image in configured storage backend
    - Creates audit log entry with actor and target details

    ## Permissions
    - **Required Role**: Admin only
    - Authentication via JWT in Authorization header
    - Audit logged with actor_id and target_user_id

    ## Path Parameters
    - `user_id` (int): Target user's unique identifier

    ## Request Body
    - `file` (multipart/form-data): Image file upload
    - Supported formats: JPG, PNG, GIF, WebP
    - Maximum size: Configured in AvatarService

    ## Response (AvatarResponse)
    - `url` (str): URL to the uploaded avatar image
    - `updated_at` (datetime): Timestamp of the upload

    ## Rate Limiting
    - **Limit**: 10 requests per minute per IP
    - Prevents abuse of file upload resources

    ## Error Responses
    - `400 Bad Request`: Invalid file format or size
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: User is not an admin
    - `404 Not Found`: User ID does not exist
    - `413 Payload Too Large`: File exceeds size limit
    - `422 Unprocessable Entity`: Invalid file type
    - `429 Too Many Requests`: Rate limit exceeded
    - `500 Internal Server Error`: Storage or server error

    ## Example Usage
    ```bash
    curl -X PATCH "http://localhost:8000/api/admin/users/42/avatar" \\
         -H "Authorization: Bearer {admin_token}" \\
         -F "file=@profile.jpg"
    ```
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    service = AvatarService(db=db)
    response = await service.upload_for_user(user=target_user, upload=file)

    audit_logger.info(
        "Admin %s updated avatar for user %s",
        current_user.email,
        target_user.email,
        extra={
            "actor_id": current_user.id,
            "target_user_id": target_user.id,
            "target_user_email": target_user.email,
        },
    )
    return response


@router.delete("/users/{user_id}")
@limiter.limit("20/minute")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Soft delete user (admin only) - sets is_active to False."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Prevent deleting the last active admin
    if user.role == "admin" and user.is_active:
        other_active_admins = (
            db.query(User)
            .filter(
                User.role == "admin",
                User.is_active.is_(True),
                User.deleted_at.is_(None),
                User.id != user.id,
            )
            .count()
        )
        if other_active_admins == 0:
            logger.warning(
                f"Admin {current_user.email} attempted to delete last admin {user.email}"
            )
            raise HTTPException(
                status_code=400, detail="Cannot remove the last active admin"
            )

    try:
        # Soft delete instead of hard delete
        user.is_active = False
        db.commit()

        logger.warning(f"Admin {current_user.email} soft-deleted user {user_id} ({user.email})")
        return {"message": "User deactivated"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


# ============================================================================
# Tutor Approval Workflow
# ============================================================================


@router.get("/tutors/pending", response_model=PaginatedResponse[TutorProfileResponse])
@limiter.limit("60/minute")
async def list_pending_tutors(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of tutors pending approval (admin only)."""
    try:
        query = (
            db.query(TutorProfile)
            .filter(TutorProfile.profile_status.in_(["pending_approval", "under_review"]))
            .order_by(TutorProfile.created_at.desc())
        )

        result = paginate(query, page=page, page_size=page_size)
        logger.info(f"Admin {current_user.email} viewed pending tutors (page {page})")
        return result
    except Exception as e:
        logger.error(f"Error retrieving pending tutors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending tutors")


@router.get("/tutors/approved", response_model=PaginatedResponse[TutorProfileResponse])
@limiter.limit("60/minute")
async def list_approved_tutors(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of approved tutors (admin only)."""
    try:
        query = (
            db.query(TutorProfile)
            .filter(TutorProfile.profile_status == "approved")
            .order_by(TutorProfile.approved_at.desc())
        )

        result = paginate(query, page=page, page_size=page_size)
        logger.info(f"Admin {current_user.email} viewed approved tutors (page {page})")
        return result
    except Exception as e:
        logger.error(f"Error retrieving approved tutors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve approved tutors")


@router.post("/tutors/{tutor_id}/approve", response_model=TutorProfileResponse)
@limiter.limit("30/minute")
async def approve_tutor(
    request: Request,
    tutor_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Approve a tutor profile (admin only)."""
    tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == tutor_id).first()
    if not tutor_profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    if tutor_profile.profile_status == "approved":
        raise HTTPException(status_code=400, detail="Tutor already approved")

    try:
        # Update profile status
        tutor_profile.is_approved = True
        tutor_profile.profile_status = "approved"
        tutor_profile.approved_at = datetime.now(UTC)
        tutor_profile.approved_by = current_user.id
        tutor_profile.rejection_reason = None

        # Create notification for tutor
        notification = Notification(
            user_id=tutor_profile.user_id,
            type="profile_approved",
            title="Your Tutor Profile is Live!",
            message="Congratulations! Your tutor profile has been approved and is now visible to students. You can start receiving bookings.",
            link="/tutor/profile",
            is_read=False,
        )
        db.add(notification)

        db.commit()
        db.refresh(tutor_profile)

        logger.info(f"Admin {current_user.email} approved tutor profile {tutor_id}")
        return tutor_profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving tutor {tutor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve tutor")


@router.post("/tutors/{tutor_id}/reject", response_model=TutorProfileResponse)
@limiter.limit("30/minute")
async def reject_tutor(
    request: Request,
    tutor_id: int,
    payload: TutorRejectionRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Reject a tutor profile (admin only)."""
    tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == tutor_id).first()
    if not tutor_profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    if tutor_profile.profile_status == "rejected":
        raise HTTPException(status_code=400, detail="Tutor already rejected")

    # Sanitize rejection reason to prevent XSS
    rejection_reason = sanitize_text_input(payload.rejection_reason, max_length=500)
    if not rejection_reason or len(rejection_reason.strip()) < 10:
        raise HTTPException(status_code=400, detail="Rejection reason must be at least 10 characters")

    try:
        # Update profile status
        tutor_profile.is_approved = False
        tutor_profile.profile_status = "rejected"
        tutor_profile.rejection_reason = rejection_reason
        tutor_profile.approved_at = None
        tutor_profile.approved_by = None

        # Create notification for tutor with sanitized message
        notification = Notification(
            user_id=tutor_profile.user_id,
            type="profile_rejected",
            title="Profile Requires Revisions",
            message=f"Your tutor profile needs some changes: {rejection_reason}",
            link="/tutor/profile",
            is_read=False,
        )
        db.add(notification)

        db.commit()
        db.refresh(tutor_profile)

        logger.info(f"Admin {current_user.email} rejected tutor profile {tutor_id}")
        return tutor_profile
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting tutor {tutor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject tutor")


# ============================================================================
# Dashboard Statistics & Analytics
# ============================================================================


class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    totalUsers: int
    activeTutors: int
    totalSessions: int
    revenue: float
    satisfaction: float
    completionRate: float


class ActivityItem(BaseModel):
    """Recent activity item."""

    id: int
    user: str
    action: str
    time: str
    type: str


class SessionMetric(BaseModel):
    """Session metric response."""

    metric: str
    value: str
    change: str


class SubjectDistribution(BaseModel):
    """Subject distribution data."""

    subject: str
    value: int
    color: str


class MonthlyData(BaseModel):
    """Monthly revenue and sessions data."""

    month: str
    revenue: float
    sessions: int


class UserGrowthData(BaseModel):
    """User growth data."""

    month: str
    tutors: int
    students: int


@router.get("/dashboard/stats", response_model=DashboardStats)
@limiter.limit("60/minute")
async def get_dashboard_stats(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics (admin only)."""
    try:
        # Total users count
        total_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0

        # Active tutors (approved profiles)
        active_tutors = (
            db.query(func.count(TutorProfile.id))
            .filter(
                and_(
                    TutorProfile.is_approved.is_(True),
                    TutorProfile.profile_status == "approved",
                )
            )
            .scalar()
            or 0
        )

        # Total sessions (SCHEDULED or completed)
        total_sessions = (
            db.query(func.count(Booking.id)).filter(
                Booking.session_state.in_(["SCHEDULED", "ENDED"])
            ).scalar() or 0
        )

        # Revenue (sum of completed bookings)
        revenue = db.query(func.sum(Booking.total_amount)).filter(
            Booking.session_state == "ENDED",
            Booking.session_outcome == "COMPLETED"
        ).scalar() or 0.0

        # Average satisfaction (rating)
        avg_rating = db.query(func.avg(Review.rating)).filter(Review.is_public.is_(True)).scalar() or 0.0

        # Completion rate (completed vs all bookings)
        total_bookings = db.query(func.count(Booking.id)).scalar() or 1
        completed_bookings = db.query(func.count(Booking.id)).filter(
            Booking.session_state == "ENDED",
            Booking.session_outcome == "COMPLETED"
        ).scalar() or 0
        completion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0

        logger.info(f"Admin {current_user.email} fetched dashboard stats")

        return DashboardStats(
            totalUsers=total_users,
            activeTutors=active_tutors,
            totalSessions=total_sessions,
            revenue=float(revenue),
            satisfaction=round(float(avg_rating), 1),
            completionRate=round(completion_rate, 0),
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")


@router.get("/dashboard/recent-activities", response_model=list[ActivityItem])
@limiter.limit("60/minute")
async def get_recent_activities(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get recent platform activities (admin only)."""
    try:
        activities = []

        # Get recent bookings
        recent_bookings = (
            db.query(Booking)
            .join(User, Booking.student_id == User.id)
            .options(joinedload(Booking.student))
            .filter(Booking.session_state.in_(["SCHEDULED", "ENDED"]))
            .order_by(desc(Booking.created_at))
            .limit(limit // 2)
            .all()
        )

        for booking in recent_bookings:
            student_name = booking.student.email.split("@")[0] if booking.student else "Unknown"
            is_completed = booking.session_state == "ENDED" and booking.session_outcome == "COMPLETED"
            action = "completed a session" if is_completed else "scheduled a session"
            time_diff = datetime.now(UTC) - booking.created_at
            time_str = format_time_ago(time_diff)

            activities.append(
                {
                    "id": booking.id,
                    "user": student_name.title(),
                    "action": action,
                    "time": time_str,
                    "type": "success" if is_completed else "info",
                }
            )

        # Get recent user registrations
        recent_users = (
            db.query(User)
            .filter(User.role.in_(["student", "tutor"]))
            .order_by(desc(User.created_at))
            .limit(limit // 2)
            .all()
        )

        for user in recent_users:
            user_name = user.email.split("@")[0]
            action = "joined as new tutor" if user.role == "tutor" else "registered as student"
            time_diff = datetime.now(UTC) - user.created_at
            time_str = format_time_ago(time_diff)

            activities.append(
                {
                    "id": user.id + 10000,  # Offset to avoid ID collision
                    "user": user_name.title(),
                    "action": action,
                    "time": time_str,
                    "type": "info",
                }
            )

        # Sort by most recent and limit
        activities_sorted = sorted(
            activities,
            key=lambda x: x["id"] if x["id"] < 10000 else x["id"] - 10000,
            reverse=True,
        )[:limit]

        logger.info(f"Admin {current_user.email} fetched recent activities")
        return activities_sorted
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent activities")


@router.get("/dashboard/upcoming-sessions", response_model=list[BookingResponse])
@limiter.limit("60/minute")
async def get_upcoming_sessions(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get upcoming sessions (admin only)."""
    try:
        now = datetime.now(UTC)
        upcoming = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.start_time >= now,
                    Booking.session_state.in_(["REQUESTED", "SCHEDULED"]),
                )
            )
            .order_by(Booking.start_time.asc())
            .limit(limit)
            .all()
        )

        logger.info(f"Admin {current_user.email} fetched upcoming sessions")
        return upcoming
    except Exception as e:
        logger.error(f"Error fetching upcoming sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch upcoming sessions")


@router.get("/dashboard/session-metrics", response_model=list[SessionMetric])
@limiter.limit("60/minute")
async def get_session_metrics(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get session metrics (admin only)."""
    try:
        # Calculate current month and previous month
        now = datetime.now(UTC)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        # Current month bookings
        current_bookings = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.created_at >= current_month_start,
                    Booking.session_state.in_(["SCHEDULED", "ENDED"]),
                )
            )
            .all()
        )

        # Previous month bookings
        previous_bookings = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.created_at >= previous_month_start,
                    Booking.created_at < current_month_start,
                    Booking.session_state.in_(["SCHEDULED", "ENDED"]),
                )
            )
            .all()
        )

        # Average session duration
        avg_duration_current = calculate_avg_duration(current_bookings)
        avg_duration_previous = calculate_avg_duration(previous_bookings)
        duration_change = avg_duration_current - avg_duration_previous if avg_duration_previous > 0 else 0

        # Completion rate
        total_current = len(current_bookings)
        completed_current = len([
            b for b in current_bookings
            if b.session_state == "ENDED" and b.session_outcome == "COMPLETED"
        ])
        completion_rate = (completed_current / total_current * 100) if total_current > 0 else 0

        total_previous = len(previous_bookings)
        completed_previous = len([
            b for b in previous_bookings
            if b.session_state == "ENDED" and b.session_outcome == "COMPLETED"
        ])
        completion_rate_previous = (completed_previous / total_previous * 100) if total_previous > 0 else 0
        completion_change = completion_rate - completion_rate_previous

        # Average rating
        current_reviews = db.query(Review).filter(Review.created_at >= current_month_start).all()
        avg_rating_current = sum(r.rating for r in current_reviews) / len(current_reviews) if current_reviews else 0
        previous_reviews = (
            db.query(Review)
            .filter(
                and_(
                    Review.created_at >= previous_month_start,
                    Review.created_at < current_month_start,
                )
            )
            .all()
        )
        avg_rating_previous = sum(r.rating for r in previous_reviews) / len(previous_reviews) if previous_reviews else 0
        rating_change = avg_rating_current - avg_rating_previous

        metrics = [
            SessionMetric(
                metric="Avg Session Duration",
                value=f"{int(avg_duration_current)} min",
                change=(f"+{int(duration_change)} min" if duration_change >= 0 else f"{int(duration_change)} min"),
            ),
            SessionMetric(
                metric="Completion Rate",
                value=f"{int(completion_rate)}%",
                change=(f"+{int(completion_change)}%" if completion_change >= 0 else f"{int(completion_change)}%"),
            ),
            SessionMetric(
                metric="Avg Rating",
                value=f"{avg_rating_current:.1f}/5",
                change=(f"+{rating_change:.1f}" if rating_change >= 0 else f"{rating_change:.1f}"),
            ),
            SessionMetric(
                metric="Response Time",
                value="2.1 min",
                change="-0.3 min",
            ),
        ]

        logger.info(f"Admin {current_user.email} fetched session metrics")
        return metrics
    except Exception as e:
        logger.error(f"Error fetching session metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session metrics")


@router.get("/dashboard/subject-distribution", response_model=list[SubjectDistribution])
@limiter.limit("60/minute")
async def get_subject_distribution(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get subject distribution (admin only)."""
    try:
        # Get booking counts by subject
        subject_counts = (
            db.query(Subject.name, func.count(Booking.id).label("count"))
            .join(Booking, Booking.subject_id == Subject.id)
            .filter(Booking.session_state.in_(["SCHEDULED", "ENDED"]))
            .group_by(Subject.name)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        colors = ["#8B5CF6", "#EC4899", "#3B82F6", "#10B981", "#F59E0B"]
        total = sum(count for _, count in subject_counts)

        distribution = []
        for idx, (name, count) in enumerate(subject_counts):
            percentage = int(count / total * 100) if total > 0 else 0
            distribution.append(
                SubjectDistribution(
                    subject=name,
                    value=percentage,
                    color=colors[idx] if idx < len(colors) else "#6B7280",
                )
            )

        logger.info(f"Admin {current_user.email} fetched subject distribution")
        return distribution
    except Exception as e:
        logger.error(f"Error fetching subject distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subject distribution")


@router.get("/dashboard/monthly-revenue", response_model=list[MonthlyData])
@limiter.limit("60/minute")
async def get_monthly_revenue(
    request: Request,
    months: int = Query(6, ge=1, le=12),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get monthly revenue and sessions data (admin only)."""
    try:
        now = datetime.now(UTC)
        data = []

        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            revenue = (
                db.query(func.sum(Booking.total_amount))
                .filter(
                    and_(
                        Booking.created_at >= month_start,
                        Booking.created_at <= month_end,
                        Booking.session_state == "ENDED",
                        Booking.session_outcome == "COMPLETED",
                    )
                )
                .scalar()
                or 0.0
            )

            sessions = (
                db.query(func.count(Booking.id))
                .filter(
                    and_(
                        Booking.created_at >= month_start,
                        Booking.created_at <= month_end,
                        Booking.session_state.in_(["SCHEDULED", "ENDED"]),
                    )
                )
                .scalar()
                or 0
            )

            month_name = month_start.strftime("%b")
            data.append(
                MonthlyData(
                    month=month_name,
                    revenue=float(revenue),
                    sessions=sessions,
                )
            )

        logger.info(f"Admin {current_user.email} fetched monthly revenue data")
        return data
    except Exception as e:
        logger.error(f"Error fetching monthly revenue: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch monthly revenue")


@router.get("/dashboard/user-growth", response_model=list[UserGrowthData])
@limiter.limit("60/minute")
async def get_user_growth(
    request: Request,
    months: int = Query(6, ge=1, le=12),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get user growth data (admin only)."""
    try:
        now = datetime.now(UTC)
        data = []

        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            tutors = (
                db.query(func.count(User.id))
                .filter(
                    and_(
                        User.role == "tutor",
                        User.created_at < month_end,
                        User.is_active.is_(True),
                    )
                )
                .scalar()
                or 0
            )

            students = (
                db.query(func.count(User.id))
                .filter(
                    and_(
                        User.role == "student",
                        User.created_at < month_end,
                        User.is_active.is_(True),
                    )
                )
                .scalar()
                or 0
            )

            month_name = month_start.strftime("%b")
            data.append(
                UserGrowthData(
                    month=month_name,
                    tutors=tutors,
                    students=students,
                )
            )

        logger.info(f"Admin {current_user.email} fetched user growth data")
        return data
    except Exception as e:
        logger.error(f"Error fetching user growth: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user growth")


# ============================================================================
# Helper Functions
# ============================================================================


def format_time_ago(time_diff: timedelta) -> str:
    """Format timedelta to human-readable string."""
    seconds = int(time_diff.total_seconds())
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"


def calculate_avg_duration(bookings: list) -> float:
    """Calculate average duration of bookings in minutes."""
    if not bookings:
        return 0.0

    total_minutes = 0
    for booking in bookings:
        if booking.start_time and booking.end_time:
            duration = (booking.end_time - booking.start_time).total_seconds() / 60
            total_minutes += duration

    return total_minutes / len(bookings) if bookings else 0.0
