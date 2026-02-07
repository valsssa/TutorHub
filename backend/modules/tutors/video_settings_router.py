"""
Tutor Video Meeting Settings Router

Handles configuration of video meeting provider preferences for tutors.
"""

import logging
import re
from datetime import datetime

from core.datetime_utils import utc_now

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from core.dependencies import DatabaseSession, TutorUser
from core.rate_limiting import limiter
from models import TutorProfile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tutor/settings/video",
    tags=["tutor-settings"],
)


# ============================================================================
# Schemas
# ============================================================================


class VideoProviderEnum:
    """Valid video provider options."""
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    TEAMS = "teams"
    CUSTOM = "custom"
    MANUAL = "manual"

    ALL = [ZOOM, GOOGLE_MEET, TEAMS, CUSTOM, MANUAL]


class VideoSettingsResponse(BaseModel):
    """Video meeting settings response."""
    preferred_video_provider: str
    custom_meeting_url_template: str | None = None
    video_provider_configured: bool = False
    zoom_available: bool = False
    google_calendar_connected: bool = False


class VideoSettingsUpdateRequest(BaseModel):
    """Request to update video meeting settings."""
    preferred_video_provider: str
    custom_meeting_url_template: str | None = None

    @field_validator("preferred_video_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in VideoProviderEnum.ALL:
            raise ValueError(f"Invalid provider. Must be one of: {', '.join(VideoProviderEnum.ALL)}")
        return v

    @field_validator("custom_meeting_url_template")
    @classmethod
    def validate_url_template(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

        if not url_pattern.match(v):
            raise ValueError("Invalid URL format. Must be a valid HTTP/HTTPS URL.")

        return v


class VideoProviderOption(BaseModel):
    """Video provider option for frontend display."""
    value: str
    label: str
    description: str
    requires_setup: bool = False
    is_available: bool = True


class VideoProvidersListResponse(BaseModel):
    """List of available video providers."""
    providers: list[VideoProviderOption]
    current_provider: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "",
    response_model=VideoSettingsResponse,
    summary="Get video meeting settings",
)
@limiter.limit("30/minute")
async def get_video_settings(
    request: Request,
    current_user: TutorUser,
    db: DatabaseSession,
) -> VideoSettingsResponse:
    """Get tutor's video meeting provider settings."""
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == current_user.id
    ).first()

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found",
        )

    # Check if Zoom is available (Server-to-Server OAuth configured)
    from core.config import settings
    zoom_available = bool(
        settings.ZOOM_CLIENT_ID
        and settings.ZOOM_CLIENT_SECRET
        and settings.ZOOM_ACCOUNT_ID
    )

    # Check if Google Calendar is connected
    google_calendar_connected = bool(current_user.google_calendar_refresh_token)

    return VideoSettingsResponse(
        preferred_video_provider=tutor_profile.preferred_video_provider or "zoom",
        custom_meeting_url_template=tutor_profile.custom_meeting_url_template,
        video_provider_configured=tutor_profile.video_provider_configured or False,
        zoom_available=zoom_available,
        google_calendar_connected=google_calendar_connected,
    )


@router.put(
    "",
    response_model=VideoSettingsResponse,
    summary="Update video meeting settings",
)
@limiter.limit("20/minute")
async def update_video_settings(
    request: Request,
    settings_update: VideoSettingsUpdateRequest,
    current_user: TutorUser,
    db: DatabaseSession,
) -> VideoSettingsResponse:
    """
    Update tutor's video meeting provider settings.

    Validates that the selected provider is properly configured:
    - zoom: Always available (Server-to-Server OAuth)
    - google_meet: Requires Google Calendar connection
    - teams: Requires custom_meeting_url_template with Teams URL
    - custom: Requires custom_meeting_url_template
    - manual: Always available (tutor provides URL for each booking)
    """
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == current_user.id
    ).first()

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found",
        )

    provider = settings_update.preferred_video_provider
    url_template = settings_update.custom_meeting_url_template
    is_configured = False

    # Validate provider-specific requirements
    if provider == VideoProviderEnum.GOOGLE_MEET:
        if not current_user.google_calendar_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Meet requires a connected Google Calendar. Please connect your calendar first.",
            )
        is_configured = True

    elif provider == VideoProviderEnum.TEAMS:
        if not url_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Microsoft Teams requires a meeting URL. Please provide your Teams meeting link.",
            )
        # Validate Teams URL
        if not _is_valid_teams_url(url_template):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Microsoft Teams URL. Please provide a valid Teams meeting link.",
            )
        is_configured = True

    elif provider == VideoProviderEnum.CUSTOM:
        if not url_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom provider requires a meeting URL. Please provide your meeting link.",
            )
        is_configured = True

    elif provider == VideoProviderEnum.ZOOM:
        # Zoom is always available via Server-to-Server OAuth
        from core.config import settings as app_settings
        zoom_available = bool(
            app_settings.ZOOM_CLIENT_ID
            and app_settings.ZOOM_CLIENT_SECRET
            and app_settings.ZOOM_ACCOUNT_ID
        )
        if not zoom_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Zoom integration is not configured on this platform.",
            )
        is_configured = True

    elif provider == VideoProviderEnum.MANUAL:
        # Manual is always available
        is_configured = True

    # Update profile
    tutor_profile.preferred_video_provider = provider
    tutor_profile.custom_meeting_url_template = url_template
    tutor_profile.video_provider_configured = is_configured
    tutor_profile.updated_at = utc_now()

    db.commit()
    db.refresh(tutor_profile)

    logger.info(
        "Updated video settings for tutor %d: provider=%s, configured=%s",
        tutor_profile.id,
        provider,
        is_configured,
    )

    # Check current availability
    from core.config import settings as app_settings
    zoom_available = bool(
        app_settings.ZOOM_CLIENT_ID
        and app_settings.ZOOM_CLIENT_SECRET
        and app_settings.ZOOM_ACCOUNT_ID
    )

    return VideoSettingsResponse(
        preferred_video_provider=tutor_profile.preferred_video_provider,
        custom_meeting_url_template=tutor_profile.custom_meeting_url_template,
        video_provider_configured=tutor_profile.video_provider_configured,
        zoom_available=zoom_available,
        google_calendar_connected=bool(current_user.google_calendar_refresh_token),
    )


@router.get(
    "/providers",
    response_model=VideoProvidersListResponse,
    summary="List available video providers",
)
@limiter.limit("30/minute")
async def list_video_providers(
    request: Request,
    current_user: TutorUser,
    db: DatabaseSession,
) -> VideoProvidersListResponse:
    """
    Get list of available video providers with their status.

    Returns provider options with availability based on:
    - Platform configuration (Zoom Server-to-Server OAuth)
    - User's connected services (Google Calendar)
    """
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.user_id == current_user.id
    ).first()

    current_provider = tutor_profile.preferred_video_provider if tutor_profile else "zoom"

    # Check availability
    from core.config import settings as app_settings
    zoom_available = bool(
        app_settings.ZOOM_CLIENT_ID
        and app_settings.ZOOM_CLIENT_SECRET
        and app_settings.ZOOM_ACCOUNT_ID
    )
    google_calendar_connected = bool(current_user.google_calendar_refresh_token)

    providers = [
        VideoProviderOption(
            value="zoom",
            label="Zoom",
            description="Automatic Zoom meeting links. Recommended for most tutors.",
            requires_setup=False,
            is_available=zoom_available,
        ),
        VideoProviderOption(
            value="google_meet",
            label="Google Meet",
            description="Google Meet links via your connected calendar.",
            requires_setup=True,
            is_available=google_calendar_connected,
        ),
        VideoProviderOption(
            value="teams",
            label="Microsoft Teams",
            description="Use your personal Teams meeting room link.",
            requires_setup=True,
            is_available=True,
        ),
        VideoProviderOption(
            value="custom",
            label="Custom URL",
            description="Use any video platform (Jitsi, Whereby, etc.) with your own link.",
            requires_setup=True,
            is_available=True,
        ),
        VideoProviderOption(
            value="manual",
            label="Manual",
            description="Provide a meeting link manually for each booking.",
            requires_setup=False,
            is_available=True,
        ),
    ]

    return VideoProvidersListResponse(
        providers=providers,
        current_provider=current_provider,
    )


def _is_valid_teams_url(url: str) -> bool:
    """Validate Microsoft Teams URL format."""
    teams_patterns = [
        r'teams\.microsoft\.com',
        r'teams\.live\.com',
    ]

    return any(re.search(pattern, url, re.IGNORECASE) for pattern in teams_patterns)
