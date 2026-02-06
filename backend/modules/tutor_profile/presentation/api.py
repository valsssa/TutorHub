"""FastAPI router for tutor profile module."""

import json
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.dependencies import get_current_tutor_user, get_current_user
from core.pagination import PaginatedResponse, PaginationParams
from core.rate_limiting import limiter
from core.storage import _extract_key_from_url, _s3_client
from database import get_db
from models import User
from schemas import (
    TutorAboutUpdate,
    TutorAvailabilityBulkUpdate,
    TutorCertificationInput,
    TutorDescriptionUpdate,
    TutorEducationInput,
    TutorPricingUpdate,
    TutorProfileResponse,
    TutorPublicProfile,
    TutorSubjectInput,
    TutorVideoUpdate,
)

from ..application.services import TutorProfileService
from ..infrastructure.repositories import SqlAlchemyTutorProfileRepository

router = APIRouter(prefix="/tutors", tags=["tutors"])

# Initialize rate limiter

service = TutorProfileService(SqlAlchemyTutorProfileRepository())


@router.get(
    "/me/profile",
    response_model=TutorProfileResponse,
    summary="Get authenticated tutor's complete profile",
    description="""
Retrieve the complete tutor profile for the currently authenticated tutor user.

## Business Logic
- Returns full profile including all sections: about, education, certifications, subjects, availability
- Includes approval status and completion percentage
- Only accessible by users with 'tutor' role
- Automatically creates profile if it doesn't exist (lazy initialization)

## Authorization
- **Required Role**: Tutor
- Dependency: `get_current_tutor_user` validates JWT and role

## Use Cases
- Tutor dashboard profile display
- Profile editing form initialization
- Profile completion status check

## Response Fields
- `id`: Profile ID (auto-generated)
- `user_id`: Associated user account ID
- `is_approved`: Admin approval status (PENDING/APPROVED/REJECTED)
- `completion_percentage`: Profile completeness (0-100%)
- `hourly_rate`: Current hourly rate in USD
- `total_sessions`: Lifetime completed bookings count
- `average_rating`: Average review rating (1.0-5.0)
- `about`, `education`, `certifications`, `subjects`, `availability`: Profile sections

## Security
- Rate limited to 30 requests/minute per IP
- JWT token required in Authorization header
- Only returns own profile (no access to other tutors' private data)
    """,
    responses={
        200: {
            "description": "Profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 42,
                        "is_approved": True,
                        "completion_percentage": 85,
                        "hourly_rate": 50.00,
                        "total_sessions": 127,
                        "average_rating": 4.8,
                        "about": {
                            "title": "Experienced Math Tutor",
                            "headline": "10+ years teaching calculus",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized - Missing or invalid JWT token",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        403: {
            "description": "Forbidden - User is not a tutor",
            "content": {"application/json": {"example": {"detail": "Only tutors can access this endpoint"}}},
        },
        429: {
            "description": "Rate limit exceeded (30 requests/minute)",
            "content": {"application/json": {"example": {"detail": "Rate limit exceeded"}}},
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Failed to retrieve profile"}}},
        },
    },
)
async def get_my_profile(
    request: Request,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Retrieve the authenticated tutor's profile."""
    return service.get_profile_by_user(db, current_user.id)


@router.patch("/me/about", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def update_about_section(
    request: Request,
    payload: TutorAboutUpdate,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Update tutor about section."""
    return service.update_about(db, current_user.id, payload)


@router.put("/me/certifications", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def replace_certifications_section(
    request: Request,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Replace tutor certifications."""
    form = await request.form()
    raw_payload = form.get("certifications")
    if raw_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing certifications payload",
        )
    try:
        payload_data = json.loads(raw_payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid certifications payload",
        )

    certifications = [TutorCertificationInput(**item) for item in payload_data]
    file_map: dict[int, UploadFile] = {}
    for key, value in form.multi_items():
        if key.startswith("file_") and isinstance(value, UploadFile):
            try:
                index = int(key.split("_", 1)[1])
            except (IndexError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file key '{key}'",
                )
            file_map[index] = value

    for index in file_map:
        if index < 0 or index >= len(certifications):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File index out of range",
            )

    return await service.replace_certifications(db, current_user.id, certifications, file_map)


@router.put("/me/education", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def replace_education_section(
    request: Request,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Replace tutor education history."""
    form = await request.form()
    raw_payload = form.get("education")
    if raw_payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing education payload")
    try:
        payload_data = json.loads(raw_payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid education payload")

    education_items = [TutorEducationInput(**item) for item in payload_data]
    file_map: dict[int, UploadFile] = {}
    for key, value in form.multi_items():
        if key.startswith("file_") and isinstance(value, UploadFile):
            try:
                index = int(key.split("_", 1)[1])
            except (IndexError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file key '{key}'",
                )
            file_map[index] = value

    for index in file_map:
        if index < 0 or index >= len(education_items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File index out of range",
            )

    return await service.replace_educations(db, current_user.id, education_items, file_map)


@router.put("/me/subjects", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def replace_subjects_section(
    request: Request,
    payload: list[TutorSubjectInput],
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Replace tutor subject specialisations."""
    return service.replace_subjects(db, current_user.id, payload)


@router.patch("/me/description", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def update_description_section(
    request: Request,
    payload: TutorDescriptionUpdate,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Update long description."""
    return service.update_description(db, current_user.id, payload)


@router.patch("/me/video", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def update_video_section(
    request: Request,
    payload: TutorVideoUpdate,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Update intro video."""
    return service.update_video(db, current_user.id, payload)


@router.patch("/me/photo", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def update_profile_photo(
    request: Request,
    profile_photo: UploadFile,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Update tutor profile photo."""
    return await service.update_profile_photo(db, current_user.id, profile_photo)


@router.patch("/me/pricing", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def update_pricing_section(
    request: Request,
    payload: TutorPricingUpdate,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Update pricing details."""
    return service.update_pricing(db, current_user.id, payload)


@router.put("/me/availability", response_model=TutorProfileResponse)
@limiter.limit("10/minute")
async def replace_availability_section(
    request: Request,
    payload: TutorAvailabilityBulkUpdate,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Replace tutor availability slots."""
    return service.replace_availability(db, current_user.id, payload)


@router.post("/me/submit", response_model=TutorProfileResponse)
@limiter.limit("5/minute")
async def submit_profile_for_review(
    request: Request,
    current_user=Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Submit tutor profile for admin review."""
    return service.submit_for_review(db, current_user.id)


@router.get("", response_model=PaginatedResponse[TutorPublicProfile])
@limiter.limit("60/minute")
async def list_tutors(
    request: Request,
    pagination: PaginationParams = Depends(),
    subject_id: int | None = None,
    min_rate: float | None = None,
    max_rate: float | None = None,
    min_rating: float | None = None,
    min_experience: int | None = None,
    language: str | None = None,
    search_query: str | None = None,
    sort_by: str | None = None,
    db: Session = Depends(get_db),
):
    """List approved tutors with advanced filters and pagination.

    Filters:
    - subject_id: Filter by subject ID
    - min_rate, max_rate: Hourly rate range
    - min_rating: Minimum average rating
    - min_experience: Minimum years of experience
    - language: Filter by language (exact match)
    - search_query: Search in title, headline, and bio
    - sort_by: 'rating', 'rate_asc', 'rate_desc', 'experience' (default: rating)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    return service.list_public_profiles(
        db,
        pagination=pagination,
        subject_id=subject_id,
        min_rate=min_rate,
        max_rate=max_rate,
        min_rating=min_rating,
        min_experience=min_experience,
        language=language,
        search_query=search_query,
        sort_by=sort_by,
    )


@router.get("/{tutor_id}/public", response_model=TutorPublicProfile)
@limiter.limit("60/minute")
async def get_tutor_public_profile(
    request: Request,
    tutor_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve tutor's public profile by id. Public access allowed."""
    profile = service.get_public_profile_by_id(db, tutor_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    return profile


@router.get("/{tutor_id}", response_model=TutorProfileResponse)
@limiter.limit("60/minute")
async def get_tutor_profile(
    request: Request,
    tutor_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve tutor profile by id. Public access allowed."""
    profile = service.get_profile_by_id(db, tutor_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")
    return profile


@router.get("/{tutor_id}/reviews")
@limiter.limit("60/minute")
async def get_tutor_reviews(
    request: Request,
    tutor_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all public reviews for a tutor profile (alias endpoint)."""
    from models import Review

    reviews = (
        db.query(Review)
        .filter(Review.tutor_profile_id == tutor_id, Review.is_public.is_(True))
        .order_by(Review.created_at.desc())
        .all()
    )
    return reviews


@router.get("/{tutor_id}/photo")
@limiter.limit("60/minute")
async def get_tutor_photo(
    request: Request,
    tutor_id: int,
    db: Session = Depends(get_db),
):
    """Serve tutor profile photo from storage."""
    from core.storage import MINIO_BUCKET

    # Get tutor profile to find the user
    profile = service.get_profile_by_id(db, tutor_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor not found")

    # Get user to find avatar_key
    user = db.query(User).filter(User.id == profile.user_id).first()
    if not user or not user.avatar_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor photo not found")

    # Extract storage key from URL
    storage_key = _extract_key_from_url(user.avatar_key)

    if not storage_key:
        # If URL doesn't match expected format, try to construct key from tutor_profiles path
        # Handle old avatar format: /avatars/{user_id}/{filename}
        if "/avatars/" in user.avatar_key:
            # Extract filename from old URL
            parts = user.avatar_key.split("/avatars/")
            if len(parts) > 1:
                filename = parts[-1]
                storage_key = f"tutor_profiles/{profile.user_id}/photo/{filename}"
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid photo URL format")

    # Get file from MinIO
    try:
        client = _s3_client()
        response = client.get_object(Bucket=MINIO_BUCKET, Key=storage_key)
        content = response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")

        return StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found in storage"
        )
