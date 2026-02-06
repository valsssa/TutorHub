"""Favorites API endpoints."""

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.avatar_storage import build_avatar_url
from core.dependencies import StudentUser, get_db
from core.query_helpers import get_by_id_or_404
from models import FavoriteTutor, TutorProfile, TutorSubject
from modules.favorites.schemas import (
    FavoriteCheckResponse,
    FavoriteCreate,
    FavoriteResponse,
    FavoritesCheckRequest,
    FavoritesCheckResponse,
    FavoriteWithTutorResponse,
    PaginatedFavoritesResponse,
    TutorSubjectSummary,
    TutorSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("")
async def get_favorites(
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """Get favorite tutors for the current user with pagination.

    Args:
        page: Page number (default: 1, min: 1)
        page_size: Items per page (default: 20, min: 1, max: 100)

    Returns:
        Paginated response with favorites and metadata.
        For backward compatibility, the response structure includes
        items, total, page, page_size, total_pages, has_next, has_prev.
    """
    # Get total count for pagination metadata
    total = (
        db.query(func.count(FavoriteTutor.id))
        .filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.deleted_at.is_(None),
        )
        .scalar()
    ) or 0

    # Calculate offset
    offset = (page - 1) * page_size

    # Eagerly load tutor_profile with user and subjects to avoid N+1 queries
    favorites = (
        db.query(FavoriteTutor)
        .options(
            joinedload(FavoriteTutor.tutor_profile)
            .joinedload(TutorProfile.user),
            joinedload(FavoriteTutor.tutor_profile)
            .joinedload(TutorProfile.subjects)
            .joinedload(TutorSubject.subject),
        )
        .filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.deleted_at.is_(None),
        )
        .order_by(FavoriteTutor.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    logger.info(
        f"Retrieved {len(favorites)} favorites (page {page}) for user {current_user.id}"
    )

    # Build response with embedded tutor data
    items = []
    for fav in favorites:
        tutor_summary = None
        if fav.tutor_profile:
            tp = fav.tutor_profile
            # Build subjects list from relationship
            subjects = []
            for ts in tp.subjects or []:
                if ts.subject:
                    subjects.append(TutorSubjectSummary(
                        id=ts.subject.id,
                        name=ts.subject.name
                    ))

            # Build avatar URL from user's avatar_key
            avatar_key = tp.user.avatar_key if tp.user else None
            profile_photo_url = build_avatar_url(avatar_key, allow_absolute=True)

            tutor_summary = TutorSummary(
                id=tp.id,
                user_id=tp.user_id,
                first_name=tp.user.first_name if tp.user else None,
                last_name=tp.user.last_name if tp.user else None,
                title=tp.title or "",
                headline=tp.headline,
                hourly_rate=tp.hourly_rate,
                average_rating=float(tp.average_rating) if tp.average_rating else 0.0,
                total_reviews=tp.total_reviews or 0,
                total_sessions=tp.total_sessions or 0,
                profile_photo_url=profile_photo_url,
                subjects=subjects,
            )

        items.append(FavoriteWithTutorResponse(
            id=fav.id,
            student_id=fav.student_id,
            tutor_profile_id=fav.tutor_profile_id,
            created_at=fav.created_at,
            tutor=tutor_summary,
        ))

    # Use the core pagination utility pattern
    from math import ceil
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Add a tutor to favorites."""
    from fastapi import HTTPException

    # Check if tutor profile exists
    get_by_id_or_404(db, TutorProfile, favorite_data.tutor_profile_id, detail="Tutor profile not found")

    # Check for existing record (including soft-deleted)
    existing = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id == favorite_data.tutor_profile_id
    ).first()

    if existing:
        if existing.deleted_at is None:
            # Already favorited and active - return 409
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tutor is already in favorites"
            )
        # Reactivate soft-deleted favorite
        existing.deleted_at = None
        existing.deleted_by = None
        db.commit()
        db.refresh(existing)
        logger.info(f"User {current_user.id} re-favorited tutor {favorite_data.tutor_profile_id}")
        return existing

    # Create new favorite
    favorite = FavoriteTutor(
        student_id=current_user.id,
        tutor_profile_id=favorite_data.tutor_profile_id
    )

    try:
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        logger.info(f"User {current_user.id} added tutor {favorite_data.tutor_profile_id} to favorites")
        return favorite
    except IntegrityError:
        db.rollback()
        logger.warning(f"Duplicate favorite attempt by user {current_user.id} for tutor {favorite_data.tutor_profile_id}")
        # Race condition - another request created it, fetch and check
        favorite = db.query(FavoriteTutor).filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.tutor_profile_id == favorite_data.tutor_profile_id
        ).first()
        if favorite and favorite.deleted_at is not None:
            # Reactivate soft-deleted record
            favorite.deleted_at = None
            favorite.deleted_by = None
            db.commit()
            db.refresh(favorite)
        return favorite


@router.delete("/{tutor_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    tutor_profile_id: int,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Remove a tutor from favorites (soft delete)."""
    # Only find non-deleted favorites
    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id == tutor_profile_id,
        FavoriteTutor.deleted_at.is_(None)
    ).first()

    if not favorite:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    # Soft delete: set deleted_at and deleted_by
    favorite.deleted_at = datetime.now(timezone.utc)
    favorite.deleted_by = current_user.id
    db.commit()
    logger.info(f"User {current_user.id} removed tutor {tutor_profile_id} from favorites (soft delete)")


@router.post("/check", response_model=FavoritesCheckResponse)
async def check_favorites_batch(
    request: FavoritesCheckRequest,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Check which tutors from a list are in user's favorites.

    This batch endpoint is more efficient than individual checks,
    returning only the IDs that are favorited (no 404s for unfavorited tutors).
    """
    favorites = db.query(FavoriteTutor.tutor_profile_id).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id.in_(request.tutor_profile_ids),
        FavoriteTutor.deleted_at.is_(None)
    ).all()

    favorited_ids = [f[0] for f in favorites]
    logger.info(f"Batch check: {len(favorited_ids)}/{len(request.tutor_profile_ids)} favorited for user {current_user.id}")

    return FavoritesCheckResponse(favorited_ids=favorited_ids)


@router.get("/{tutor_profile_id}", response_model=FavoriteCheckResponse)
async def check_favorite(
    tutor_profile_id: int,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Check if a tutor is in user's favorites.

    Returns 200 with is_favorited=true/false instead of 404,
    avoiding unnecessary console errors in the browser.
    """
    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id == tutor_profile_id,
        FavoriteTutor.deleted_at.is_(None)
    ).first()

    if favorite:
        return FavoriteCheckResponse(is_favorited=True, favorite=favorite)
    return FavoriteCheckResponse(is_favorited=False, favorite=None)
