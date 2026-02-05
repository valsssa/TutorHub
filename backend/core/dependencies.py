"""FastAPI dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config import Roles
from core.cookie_config import get_cookie_config
from core.exceptions import AuthenticationError
from core.security import TokenManager
from core.utils import StringUtils
from database import get_db
from models import TutorProfile, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def extract_token_from_request(request: Request) -> str | None:
    """Extract access token from request.

    Priority:
    1. HttpOnly cookie (new secure method)
    2. Authorization header (legacy, for gradual migration)

    Returns None if no valid token found.
    """
    config = get_cookie_config()

    # Try cookie first (preferred)
    token = request.cookies.get(config.access_token_name)
    if token:
        return token

    # Fall back to Authorization header (legacy support)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer ") and len(auth_header) > 7:
        return auth_header[7:]  # Strip "Bearer " prefix

    return None


async def get_current_user_from_request(
    request: Request,
    db: Session,
) -> User:
    """Get the current authenticated user from request (cookie or header).

    This function extracts the token from the request using cookie-first strategy:
    1. HttpOnly cookie (preferred, more secure)
    2. Authorization header (legacy, for gradual migration)

    Validates:
    - Token signature, expiry, and type (access)
    - Password change timestamp (invalidates tokens issued before password change)
    - Role match (invalidates tokens with outdated role after demotion/promotion)

    Raises:
        HTTPException 401: If not authenticated or token is invalid
        HTTPException 403: If user is inactive
    """
    token = extract_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Validate token type is "access"
        payload = TokenManager.decode_token(token, expected_type="access")
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token payload")

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(
        User.email == StringUtils.normalize_email(email),
        User.deleted_at.is_(None),
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # Validate token was issued after any password change
    if user.password_changed_at:
        token_pwd_ts = payload.get("pwd_ts")
        if token_pwd_ts:
            if user.password_changed_at.timestamp() > token_pwd_ts:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalidated by password change, please re-login",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidated by password change, please re-login",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Validate role hasn't changed
    token_role = payload.get("role")
    if token_role and token_role != user.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token role outdated, please re-login",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token.

    Validates:
    - Token signature and expiry
    - Password change timestamp (invalidates tokens issued before password change)
    - Role match (invalidates tokens with outdated role after demotion/promotion)
    """
    # Handle missing token (auto_error=False means token can be None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = TokenManager.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token payload")

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(
        User.email == StringUtils.normalize_email(email),
        User.deleted_at.is_(None),  # Exclude soft-deleted users
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    # Validate token was issued after any password change
    if user.password_changed_at:
        token_pwd_ts = payload.get("pwd_ts")
        if token_pwd_ts:
            # token_pwd_ts is already a float timestamp from JWT
            if user.password_changed_at.timestamp() > token_pwd_ts:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalidated by password change, please re-login",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # Token was issued before password tracking was implemented,
            # but password has been changed since - invalidate
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidated by password change, please re-login",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Validate role hasn't changed (prevents stale role after demotion/promotion)
    token_role = payload.get("role")
    if token_role and token_role != user.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token role outdated, please re-login",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Get the current authenticated user from JWT token, or None if not authenticated.

    Returns None for any invalid token (including stale password/role tokens).
    """
    if not token:
        return None

    try:
        payload = TokenManager.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            return None

    except AuthenticationError:
        return None

    user = db.query(User).filter(
        User.email == StringUtils.normalize_email(email),
        User.deleted_at.is_(None),  # Exclude soft-deleted users
    ).first()
    if user is None or not user.is_active:
        return None

    # Validate token was issued after any password change
    if user.password_changed_at:
        token_pwd_ts = payload.get("pwd_ts")
        if not token_pwd_ts or user.password_changed_at.timestamp() > token_pwd_ts:
            return None

    # Validate role hasn't changed
    token_role = payload.get("role")
    if token_role and token_role != user.role:
        return None

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure user is active (alias for backward compatibility)."""
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role (or owner, which has higher privileges)."""
    if not Roles.has_admin_access(current_user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_current_owner_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require owner role (highest privilege level for business analytics)."""
    if not Roles.is_owner(current_user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return current_user


async def get_current_tutor_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require tutor role."""
    if current_user.role != Roles.TUTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tutor access required")
    return current_user


async def get_current_student_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require student role."""
    if current_user.role != Roles.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access restricted to students only")
    return current_user


async def get_current_tutor_profile(
    current_user: Annotated[User, Depends(get_current_tutor_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get tutor profile for current authenticated tutor user.

    Raises 404 if tutor doesn't have a profile yet.
    Use this dependency in tutor-only endpoints that need profile data.
    """
    from models import TutorProfile

    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found. Please complete your profile first.",
        )
    return profile


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
OwnerUser = Annotated[User, Depends(get_current_owner_user)]
TutorUser = Annotated[User, Depends(get_current_tutor_user)]
StudentUser = Annotated[User, Depends(get_current_student_user)]
DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentTutorProfile = Annotated["TutorProfile", Depends(get_current_tutor_profile)]


# =============================================================================
# Port Factory Functions (Clean Architecture)
# =============================================================================
# These factory functions provide port implementations with environment-based
# switching between real adapters and fakes for testing.

_use_fakes = False  # Set to True in tests via set_use_fakes()


def set_use_fakes(use_fakes: bool) -> None:
    """Configure whether to use fake implementations (for testing)."""
    global _use_fakes
    _use_fakes = use_fakes


def get_payment_port():
    """Get the payment port implementation."""
    if _use_fakes:
        from core.fakes import FakePayment
        return FakePayment()
    from core.adapters import StripeAdapter
    return StripeAdapter()


def get_email_port():
    """Get the email port implementation."""
    if _use_fakes:
        from core.fakes import FakeEmail
        return FakeEmail()
    from core.adapters import BrevoAdapter
    return BrevoAdapter()


def get_storage_port():
    """Get the storage port implementation."""
    if _use_fakes:
        from core.fakes import FakeStorage
        return FakeStorage()
    from core.adapters import MinIOAdapter
    return MinIOAdapter()


def get_cache_port():
    """Get the cache port implementation."""
    if _use_fakes:
        from core.fakes import FakeCache
        return FakeCache()
    from core.adapters import RedisAdapter
    return RedisAdapter()


def get_meeting_port(provider: str = "zoom"):
    """Get the meeting port implementation.

    Args:
        provider: Meeting provider ("zoom" or "google_meet")
    """
    if _use_fakes:
        from core.fakes import FakeMeeting
        from core.ports.meeting import MeetingProvider
        fake = FakeMeeting()
        if provider == "google_meet":
            fake.provider = MeetingProvider.GOOGLE_MEET
        return fake
    if provider == "zoom":
        from core.adapters import ZoomAdapter
        return ZoomAdapter()
    # Future: add GoogleMeetAdapter when implemented
    from core.adapters import ZoomAdapter
    return ZoomAdapter()


def get_calendar_port():
    """Get the calendar port implementation."""
    if _use_fakes:
        from core.fakes import FakeCalendar
        return FakeCalendar()
    from core.adapters import GoogleCalendarAdapter
    return GoogleCalendarAdapter()


# Type aliases for port dependencies
PaymentPort = Annotated["StripeAdapter", Depends(get_payment_port)]
EmailPort = Annotated["BrevoAdapter", Depends(get_email_port)]
StoragePort = Annotated["MinIOAdapter", Depends(get_storage_port)]
CachePort = Annotated["RedisAdapter", Depends(get_cache_port)]
MeetingPort = Annotated["ZoomAdapter", Depends(get_meeting_port)]
CalendarPort = Annotated["GoogleCalendarAdapter", Depends(get_calendar_port)]
