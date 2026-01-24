"""Students API routes."""

import logging
import os
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.dependencies import get_current_student_user
from database import get_db
from models import FavoriteTutor, StudentProfile, TutorProfile, User
from schemas import FavoriteTutorCreate, FavoriteTutorResponse, StudentProfileResponse, StudentProfileUpdate

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

router = APIRouter(prefix="/api/profile/student", tags=["students"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=StudentProfileResponse)
@limiter.limit("20/minute")
async def get_student_profile(
    request: Request,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Get current student's profile."""
    try:
        logger.debug(f"Fetching student profile for user: {current_user.id}")
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile:
            logger.info(f"Creating new student profile for user: {current_user.id}")
            profile = StudentProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile
    except Exception as e:
        logger.error(
            f"Error fetching student profile for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student profile",
        )


@router.patch("/me", response_model=StudentProfileResponse)
@limiter.limit("10/minute")
async def update_student_profile(
    request: Request,
    update_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Update student profile."""
    try:
        logger.info(f"Updating student profile for user: {current_user.id}")
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile:
            logger.info(f"Creating new student profile for user: {current_user.id}")
            profile = StudentProfile(user_id=current_user.id)
            db.add(profile)

        # Update only provided fields (sanitization handled by Pydantic)
        # NOTE: first_name/last_name removed from StudentProfile in Phase 1.2 - names now stored in users table
        update_fields = update_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(profile, field, value)

        # Update timestamp in application code (no DB triggers)
        from datetime import datetime

        profile.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(profile)
        logger.info(f"Student profile updated successfully for user: {current_user.id}")
        return profile
    except Exception as e:
        logger.error(
            f"Error updating student profile for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student profile",
        )


# ============================================================================
# Favorite Tutors Endpoints
# ============================================================================

favorites_router = APIRouter(prefix="/api/favorites", tags=["favorites"])
limiter_favorites = Limiter(key_func=get_remote_address)


@favorites_router.get("/", response_model=list[FavoriteTutorResponse])
@limiter_favorites.limit("20/minute")
async def get_favorite_tutors(
    request: Request,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Get current student's favorite tutors."""
    try:
        logger.debug(f"Fetching favorite tutors for user: {current_user.id}")
        favorites = (
            db.query(FavoriteTutor)
            .filter(FavoriteTutor.student_id == current_user.id)
            .order_by(FavoriteTutor.created_at.desc())
            .all()
        )
        return favorites
    except Exception as e:
        logger.error(
            f"Error fetching favorite tutors for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve favorite tutors",
        )


@favorites_router.post("/", response_model=FavoriteTutorResponse)
@limiter_favorites.limit("10/minute")
async def add_favorite_tutor(
    request: Request,
    favorite_data: FavoriteTutorCreate,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Add a tutor to student's favorites."""
    try:
        logger.info(f"Adding favorite tutor {favorite_data.tutor_profile_id} for user: {current_user.id}")

        # Check if tutor profile exists
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == favorite_data.tutor_profile_id).first()
        if not tutor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor profile not found",
            )

        # Check if already favorited
        existing = db.query(FavoriteTutor).filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.tutor_profile_id == favorite_data.tutor_profile_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tutor is already in favorites",
            )

        # Create favorite
        favorite = FavoriteTutor(
            student_id=current_user.id,
            tutor_profile_id=favorite_data.tutor_profile_id
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)

        logger.info(f"Favorite tutor added successfully for user: {current_user.id}")
        return favorite

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error adding favorite tutor for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite tutor",
        )


@favorites_router.delete("/{tutor_profile_id}", response_model=dict)
@limiter_favorites.limit("10/minute")
async def remove_favorite_tutor(
    request: Request,
    tutor_profile_id: int,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Remove a tutor from student's favorites."""
    try:
        logger.info(f"Removing favorite tutor {tutor_profile_id} for user: {current_user.id}")

        # Find and delete the favorite
        favorite = db.query(FavoriteTutor).filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.tutor_profile_id == tutor_profile_id
        ).first()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite tutor not found",
            )

        db.delete(favorite)
        db.commit()

        logger.info(f"Favorite tutor removed successfully for user: {current_user.id}")
        return {"message": "Favorite tutor removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error removing favorite tutor for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite tutor",
        )


@favorites_router.get("/{tutor_profile_id}", response_model=FavoriteTutorResponse)
@limiter_favorites.limit("20/minute")
async def check_favorite_status(
    request: Request,
    tutor_profile_id: int,
    current_user: User = Depends(get_current_student_user),
    db: Session = Depends(get_db),
):
    """Check if a tutor is in student's favorites."""
    try:
        logger.debug(f"Checking favorite status for tutor {tutor_profile_id}, user: {current_user.id}")

        favorite = db.query(FavoriteTutor).filter(
            FavoriteTutor.student_id == current_user.id,
            FavoriteTutor.tutor_profile_id == tutor_profile_id
        ).first()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor is not in favorites",
            )

        return favorite

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error checking favorite status for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check favorite status",
        )
