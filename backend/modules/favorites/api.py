"""Favorites API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.dependencies import StudentUser, get_db
from core.query_helpers import exists_or_409, get_by_id_or_404, get_or_404
from models import FavoriteTutor, TutorProfile
from modules.favorites.schemas import FavoriteCreate, FavoriteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteResponse])
async def get_favorites(
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Get all favorite tutors for the current user."""
    favorites = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id
    ).all()

    logger.info(f"Retrieved {len(favorites)} favorites for user {current_user.id}")
    return favorites


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Add a tutor to favorites."""
    # Check if tutor profile exists
    get_by_id_or_404(db, TutorProfile, favorite_data.tutor_profile_id, detail="Tutor profile not found")

    # Check if already favorited
    exists_or_409(
        db, FavoriteTutor,
        {"student_id": current_user.id, "tutor_profile_id": favorite_data.tutor_profile_id},
        detail="Tutor is already in favorites"
    )

    # Create favorite
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
        # Race condition - another request created it
        favorite = get_or_404(
            db, FavoriteTutor,
            {"student_id": current_user.id, "tutor_profile_id": favorite_data.tutor_profile_id},
            detail="Tutor is already in favorites"
        )
        return favorite


@router.delete("/{tutor_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    tutor_profile_id: int,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Remove a tutor from favorites."""
    favorite = get_or_404(
        db, FavoriteTutor,
        {"student_id": current_user.id, "tutor_profile_id": tutor_profile_id},
        detail="Favorite not found"
    )

    db.delete(favorite)
    db.commit()
    logger.info(f"User {current_user.id} removed tutor {tutor_profile_id} from favorites")


@router.get("/{tutor_profile_id}", response_model=FavoriteResponse)
async def check_favorite(
    tutor_profile_id: int,
    current_user: StudentUser,
    db: Annotated[Session, Depends(get_db)],
):
    """Check if a tutor is in user's favorites."""
    favorite = get_or_404(
        db, FavoriteTutor,
        {"student_id": current_user.id, "tutor_profile_id": tutor_profile_id},
        detail="Tutor is not in favorites"
    )

    return favorite
