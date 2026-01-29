"""Auth API routes - Presentation layer."""

import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from core.rate_limiting import limiter

from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_current_user
from database import get_db
from models import User
from modules.auth.application.services import AuthService
from modules.users.avatar.service import AvatarService
from schemas import Token, UserCreate, UserResponse, UserSelfUpdate

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="""
**User Registration**

Creates a new user account with specified role (student/tutor/admin). By default, all new registrations create 'student' role accounts. Tutor and admin roles require backend assignment or admin approval.

**Business Logic**:
- Email normalized to lowercase and validated (RFC 5322)
- Password hashed with bcrypt (12 rounds)
- Profile created automatically based on role:
  - Student → `student_profile` record
  - Tutor → `tutor_profile` record (requires approval)
  - Admin → No profile (management access only)
- Default currency: USD, timezone: UTC (user-configurable later)
- Generates JWT token for immediate login

**Rate Limiting**: 5 requests/minute per IP to prevent abuse

**Validation Rules**:
- Email: Max 254 chars, valid format, unique
- Password: 6-128 chars (no complexity requirements in MVP)
- Role: Must be 'student', 'tutor', or 'admin' (admin requires backend assignment)

**Side Effects**:
- Sends welcome email (if email service configured)
- Creates audit log entry
- Initializes default user preferences
    """,
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 42,
                        "email": "student@example.com",
                        "role": "student",
                        "is_active": True,
                        "is_verified": False,
                        "created_at": "2025-10-21T10:30:00.000Z",
                        "updated_at": "2025-10-21T10:30:00.000Z",
                        "avatar_url": "https://api.valsa.solutions/api/avatars/default.png",
                        "currency": "USD",
                        "timezone": "UTC",
                    }
                }
            },
        },
        400: {
            "description": "Validation error - invalid email, weak password, or invalid role",
            "content": {"application/json": {"example": {"detail": "Email must not exceed 254 characters"}}},
        },
        409: {
            "description": "Conflict - email already registered",
            "content": {"application/json": {"example": {"detail": "Email already registered"}}},
        },
        429: {
            "description": "Rate limit exceeded - max 5 registrations per minute",
            "content": {"application/json": {"example": {"detail": "Rate limit exceeded"}}},
        },
    },
)
@limiter.limit("5/minute")
def register(
    request: Request,
    user: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    """Register new user (creates student or tutor based on role)."""
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Registration attempt from {client_host} for email: {user.email}")

    user_entity = service.register_user(
        email=user.email,
        password=user.password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role or "student",
        timezone=user.timezone or "UTC",
        currency=user.currency or "USD",
    )

    logger.info(f"User registered successfully: {user_entity.email}, role: {user_entity.role}")
    return UserResponse(
        id=user_entity.id,
        email=user_entity.email,
        first_name=user_entity.first_name,
        last_name=user_entity.last_name,
        role=user_entity.role,
        is_active=user_entity.is_active,
        is_verified=user_entity.is_verified,
        created_at=user_entity.created_at,
        updated_at=user_entity.updated_at,
        avatar_url=settings.AVATAR_STORAGE_DEFAULT_URL,
        currency=getattr(user_entity, "currency", "USD"),
        timezone=getattr(user_entity, "timezone", "UTC"),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User login (get JWT token)",
    description="""
**User Authentication**

Authenticates user credentials and returns JWT access token for API authorization.

**Authentication Flow**:
1. Client submits email (as username) and password via OAuth2 form
2. Server validates credentials (constant-time comparison)
3. JWT token generated with 30-minute expiry
4. Token includes user ID and role in claims

**Security Features**:
- Bcrypt password verification (constant-time)
- Rate limiting: 10 attempts/minute per IP
- Failed attempts logged for security monitoring
- Email lookup uses case-insensitive indexed search

**Token Usage**:
- Include in subsequent requests: `Authorization: Bearer <token>`
- Token expires after 30 minutes
- No refresh tokens in MVP (user must re-login)

**Common Errors**:
- 401: Invalid credentials (email not found or wrong password)
- 403: Account inactive or not verified
- 429: Too many login attempts

**OAuth2 Form Fields**:
- `username`: User's email address
- `password`: User's password
    """,
    responses={
        200: {
            "description": "Login successful - JWT token returned",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Authentication failed - invalid email or password",
            "content": {"application/json": {"example": {"detail": "Incorrect email or password"}}},
        },
        403: {
            "description": "Account is inactive or not verified",
            "content": {"application/json": {"example": {"detail": "Account is inactive"}}},
        },
        429: {
            "description": "Rate limit exceeded - max 10 login attempts per minute",
            "content": {"application/json": {"example": {"detail": "Rate limit exceeded"}}},
        },
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """Login and get JWT token."""
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Login attempt from {client_host} for email: {form_data.username}")

    token_data = service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )

    logger.info(f"User logged in successfully: {form_data.username}")
    return token_data


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
**Current User Information**

Retrieves the authenticated user's profile including avatar, preferences, and account status.

**Requires Authentication**: Must include valid JWT token in Authorization header.

**Response includes**:
- Basic user info: id, email, role
- Account status: is_active, is_verified
- Timestamps: created_at, updated_at
- Preferences: currency, timezone
- Avatar URL (default or user-uploaded)

**Use Cases**:
- Dashboard profile display
- Settings page initialization
- Role-based UI rendering
- Session validation

**Security**:
- Token validated on every request
- User data loaded fresh from database (no caching)
- Avatar URL signed if using private storage
    """,
    responses={
        200: {
            "description": "Current user profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 42,
                        "email": "student@example.com",
                        "role": "student",
                        "is_active": True,
                        "is_verified": True,
                        "created_at": "2025-10-15T08:00:00.000Z",
                        "updated_at": "2025-10-21T10:30:00.000Z",
                        "avatar_url": "https://api.valsa.solutions/api/avatars/42.jpg",
                        "currency": "EUR",
                        "timezone": "Europe/Paris",
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated - missing or invalid JWT token",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user information."""
    logger.debug(f"User info requested: {current_user.email}")
    avatar_service = AvatarService(db=db)
    avatar = await avatar_service.fetch_for_user(current_user)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=getattr(current_user, "first_name", None),
        last_name=getattr(current_user, "last_name", None),
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        currency=current_user.currency,
        timezone=current_user.timezone,
        updated_at=current_user.updated_at,
        avatar_url=avatar.avatar_url,
        preferred_language=getattr(current_user, "preferred_language", None),
        locale=getattr(current_user, "locale", None),
    )


@router.put("/me", response_model=UserResponse)
@limiter.limit("10/minute")
async def update_me(
    request: Request,
    user_data: UserSelfUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user information."""
    try:
        logger.info(f"User update requested: {current_user.email}")

        # Update allowed fields
        update_data = user_data.model_dump(exclude_unset=True)

        # Apply updates
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        # Update timestamp
        current_user.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(current_user)

        # Return updated user data
        avatar_service = AvatarService(db=db)
        avatar = await avatar_service.fetch_for_user(current_user)

        logger.info(f"User updated successfully: {current_user.email}")
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=getattr(current_user, "first_name", None),
            last_name=getattr(current_user, "last_name", None),
            role=current_user.role,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            currency=current_user.currency,
            timezone=current_user.timezone,
            updated_at=current_user.updated_at,
            avatar_url=avatar.avatar_url,
            preferred_language=getattr(current_user, "preferred_language", None),
            locale=getattr(current_user, "locale", None),
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")
