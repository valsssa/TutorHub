"""
Google OAuth/OIDC Authentication Router

Implements:
- Google OAuth2 login flow
- Account linking (connect Google to existing account)
- New user registration via Google
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core.config import settings
from core.dependencies import DatabaseSession, get_current_user_optional
from core.security import TokenManager
from models import User, UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth-oauth"],
)

# ============================================================================
# OAuth Client Setup
# ============================================================================

oauth = OAuth()

# Register Google provider
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )


# ============================================================================
# Response Schemas
# ============================================================================


class OAuthURLResponse(BaseModel):
    """OAuth authorization URL response."""
    authorization_url: str
    state: str


class OAuthTokenResponse(BaseModel):
    """OAuth login success response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    is_new_user: bool


# ============================================================================
# State Management (CSRF Protection)
# ============================================================================

# In production, use Redis for state storage
_oauth_states: dict[str, dict] = {}


def _generate_state(action: str = "login", user_id: int | None = None) -> str:
    """Generate OAuth state token for CSRF protection."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "action": action,
        "user_id": user_id,
        "created_at": datetime.now(UTC),
    }
    # Clean up old states (older than 10 minutes)
    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    for s, data in list(_oauth_states.items()):
        if data["created_at"] < cutoff:
            del _oauth_states[s]
    return state


def _validate_state(state: str) -> dict | None:
    """Validate and consume OAuth state token."""
    if state not in _oauth_states:
        return None
    data = _oauth_states.pop(state)
    # Check if expired (10 minutes)
    if datetime.now(UTC) - data["created_at"] > timedelta(minutes=10):
        return None
    return data


# ============================================================================
# Google OAuth Endpoints
# ============================================================================


@router.get(
    "/google/login",
    response_model=OAuthURLResponse,
    summary="Get Google OAuth login URL",
    description="""
**Initiate Google OAuth login flow**

Returns the Google authorization URL. Redirect the user to this URL to start the OAuth flow.

**Flow:**
1. Call this endpoint to get the authorization URL
2. Redirect user to the URL
3. User authenticates with Google
4. Google redirects to callback URL
5. Callback creates/updates user and returns JWT token
    """,
)
async def google_login_url(
    request: Request,
    redirect_uri: Annotated[str | None, Query(description="Custom redirect URI")] = None,
):
    """Get Google OAuth authorization URL."""

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured",
        )

    state = _generate_state(action="login")

    # Use configured redirect URI or custom one
    callback_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

    # Build authorization URL
    google = oauth.create_client("google")
    authorization_url = await google.create_authorization_url(
        callback_uri,
        state=state,
    )

    return OAuthURLResponse(
        authorization_url=authorization_url["url"],
        state=state,
    )


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Handles the OAuth callback from Google after user authentication.",
)
async def google_callback(
    request: Request,
    code: Annotated[str, Query(description="Authorization code from Google")],
    state: Annotated[str, Query(description="State parameter for CSRF protection")],
    db: DatabaseSession,
):
    """Handle Google OAuth callback."""

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured",
        )

    # Validate state
    state_data = _validate_state(state)
    if not state_data:
        logger.warning("Invalid or expired OAuth state")
        return RedirectResponse(
            url=f"{settings.FRONTEND_LOGIN_ERROR_URL}&reason=invalid_state"
        )

    try:
        # Exchange code for tokens
        google = oauth.create_client("google")
        token = await google.authorize_access_token(request)

        # Get user info from ID token
        user_info = token.get("userinfo")
        if not user_info:
            # Fetch from userinfo endpoint as fallback
            resp = await google.get("https://openidconnect.googleapis.com/v1/userinfo")
            user_info = resp.json()

        email = user_info.get("email")
        if not email:
            logger.error("No email in Google user info")
            return RedirectResponse(
                url=f"{settings.FRONTEND_LOGIN_ERROR_URL}&reason=no_email"
            )

        email = email.lower().strip()
        google_id = user_info.get("sub")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")
        user_info.get("picture")

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        is_new_user = False

        if user:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
                user.updated_at = datetime.now(UTC)

            # Update name if empty
            if not user.first_name:
                user.first_name = first_name
            if not user.last_name:
                user.last_name = last_name

        else:
            # Create new user
            is_new_user = True
            user = User(
                email=email,
                hashed_password="",  # OAuth users don't have password
                first_name=first_name,
                last_name=last_name,
                role="student",  # Default role for new OAuth users
                is_active=True,
                is_verified=True,  # Email verified by Google
                google_id=google_id,
            )
            db.add(user)
            db.flush()

            # Create user profile
            profile = UserProfile(
                user_id=user.id,
            )
            db.add(profile)

            logger.info(f"Created new user via Google OAuth: {email}")

        db.commit()

        # Generate JWT token
        access_token = TokenManager.create_access_token(
            data={"sub": user.email, "role": user.role}
        )

        # Redirect to frontend with token
        redirect_url = settings.FRONTEND_LOGIN_SUCCESS_URL
        params = {
            "token": access_token,
            "new_user": "true" if is_new_user else "false",
        }

        return RedirectResponse(
            url=f"{redirect_url}?{urlencode(params)}"
        )

    except Exception as e:
        logger.error(f"Google OAuth error: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{settings.FRONTEND_LOGIN_ERROR_URL}&reason=oauth_error"
        )


@router.post(
    "/google/link",
    summary="Link Google account to existing user",
    description="Link a Google account to the currently logged-in user.",
)
async def link_google_account(
    code: Annotated[str, Query(description="Authorization code from Google")],
    state: Annotated[str, Query(description="State parameter")],
    request: Request,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user_optional),
):
    """Link Google account to existing user."""

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Must be logged in to link accounts",
        )

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured",
        )

    # Validate state
    state_data = _validate_state(state)
    if not state_data or state_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    try:
        google = oauth.create_client("google")
        token = await google.authorize_access_token(request)
        user_info = token.get("userinfo", {})

        google_id = user_info.get("sub")
        google_email = user_info.get("email", "").lower()

        # Check if Google account already linked to another user
        existing = db.query(User).filter(
            User.google_id == google_id,
            User.id != current_user.id,
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Google account is already linked to another user",
            )

        # Link account
        current_user.google_id = google_id
        current_user.updated_at = datetime.now(UTC)
        db.commit()

        return {"message": "Google account linked successfully", "google_email": google_email}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking Google account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link Google account",
        )


@router.delete(
    "/google/unlink",
    summary="Unlink Google account",
    description="Remove Google account link from current user.",
)
async def unlink_google_account(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user_optional),
):
    """Unlink Google account from current user."""

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Must be logged in",
        )

    if not current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google account linked",
        )

    # Check if user has password (can still login without Google)
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink Google account. Set a password first.",
        )

    current_user.google_id = None
    current_user.updated_at = datetime.now(UTC)
    db.commit()

    return {"message": "Google account unlinked successfully"}
