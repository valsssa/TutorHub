"""Tutor student notes API routes."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from core.rate_limiting import limiter
from sqlalchemy.orm import Session

from core.dependencies import get_current_tutor_user
from database import get_db
from models import StudentNote, User
from schemas import StudentNoteResponse, StudentNoteUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutor/student-notes", tags=["tutor-student-notes"])


@router.get("/{student_id}", response_model=StudentNoteResponse | None)
@limiter.limit("30/minute")
async def get_student_note(
    request: Request,
    student_id: int,
    current_user: User = Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Get notes for a specific student (tutor only)."""
    try:
        # Verify student exists
        student = db.query(User).filter(User.id == student_id, User.role == "student").first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # Get or create note
        note = (
            db.query(StudentNote)
            .filter(
                StudentNote.tutor_id == current_user.id,
                StudentNote.student_id == student_id,
            )
            .first()
        )

        if not note:
            # Return empty note structure if doesn't exist yet
            return None

        return note

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student note: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student note",
        )


@router.put("/{student_id}", response_model=StudentNoteResponse)
@limiter.limit("20/minute")
async def update_student_note(
    request: Request,
    student_id: int,
    note_data: StudentNoteUpdate,
    current_user: User = Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Create or update notes for a specific student (tutor only)."""
    try:
        # Verify student exists
        student = db.query(User).filter(User.id == student_id, User.role == "student").first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # Get or create note
        note = (
            db.query(StudentNote)
            .filter(
                StudentNote.tutor_id == current_user.id,
                StudentNote.student_id == student_id,
            )
            .first()
        )

        if note:
            # Update existing note
            note.notes = note_data.notes
            note.updated_at = datetime.now(UTC)
        else:
            # Create new note
            note = StudentNote(
                tutor_id=current_user.id,
                student_id=student_id,
                notes=note_data.notes,
            )
            db.add(note)

        db.commit()
        db.refresh(note)

        logger.info(f"Student note updated for student {student_id} by tutor {current_user.id}")
        return note

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student note: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student note",
        )


@router.delete("/{student_id}")
@limiter.limit("10/minute")
async def delete_student_note(
    request: Request,
    student_id: int,
    current_user: User = Depends(get_current_tutor_user),
    db: Session = Depends(get_db),
):
    """Delete notes for a specific student (tutor only)."""
    try:
        note = (
            db.query(StudentNote)
            .filter(
                StudentNote.tutor_id == current_user.id,
                StudentNote.student_id == student_id,
            )
            .first()
        )

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student note not found",
            )

        db.delete(note)
        db.commit()

        logger.info(f"Student note deleted for student {student_id} by tutor {current_user.id}")
        return {"message": "Student note deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting student note: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete student note",
        )
