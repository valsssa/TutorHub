"""Favorites API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models import FavoriteTutor, TutorProfile, User
from modules.favorites.schemas import FavoriteCreate, FavoriteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteResponse])
async def get_favorites(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get all favorite tutors for the current user."""
    # Only students can have favorites
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can have favorite tutors"
        )

    favorites = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id
    ).all()

    logger.info(f"Retrieved {len(favorites)} favorites for user {current_user.id}")
    return favorites


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Add a tutor to favorites."""
    # Only students can save favorites
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can save favorite tutors"
        )

    # Check if tutor profile exists
    tutor_profile = db.query(TutorProfile).filter(
        TutorProfile.id == favorite_data.tutor_profile_id
    ).first()

    if not tutor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found"
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tutor is already in favorites"
        )


@router.delete("/{tutor_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    tutor_profile_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Remove a tutor from favorites."""
    # Only students can remove favorites
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can remove favorite tutors"
        )

    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id == tutor_profile_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    db.delete(favorite)
    db.commit()
    logger.info(f"User {current_user.id} removed tutor {tutor_profile_id} from favorites")


@router.get("/{tutor_profile_id}", response_model=FavoriteResponse)
async def check_favorite(
    tutor_profile_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Check if a tutor is in user's favorites."""
    # Only students can check favorites
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can have favorite tutors"
        )

    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == current_user.id,
        FavoriteTutor.tutor_profile_id == tutor_profile_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor is not in favorites"
        )

    return favorite
