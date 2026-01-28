"""FastAPI dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.config import Roles
from core.exceptions import AuthenticationError
from core.security import TokenManager
from database import get_db
from models import TutorProfile, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token."""
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

    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Get the current authenticated user from JWT token, or None if not authenticated."""
    if not token:
        return None

    try:
        payload = TokenManager.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            return None

    except AuthenticationError:
        return None

    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if user is None or not user.is_active:
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")
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
