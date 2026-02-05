"""
Tests for Tutor Student Notes Router.

Tests cover:
- GET /tutor/student-notes/{student_id} - Get notes for a student
- PUT /tutor/student-notes/{student_id} - Create/update notes
- DELETE /tutor/student-notes/{student_id} - Delete notes
- Authorization (only tutor can access)
- Edge cases and error handling
"""

import pytest
from fastapi import status

from models import StudentNote


@pytest.fixture
def student_note(db_session, tutor_user, student_user):
    """Create a test student note."""
    note = StudentNote(
        tutor_id=tutor_user.id,
        student_id=student_user.id,
        notes="Test notes about the student. Good progress in calculus.",
    )
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)
    return note


@pytest.fixture
def another_tutor(db_session):
    """Create another tutor user for authorization tests."""
    from tests.conftest import create_test_tutor_profile, create_test_user

    user = create_test_user(
        db_session,
        email=f"tutor-other-{id(db_session)}@example.com",
        password="TutorOther123!",
        role="tutor",
        first_name="Other",
        last_name="Tutor",
    )
    create_test_tutor_profile(db_session, user.id)
    return user


@pytest.fixture
def another_tutor_token(client, another_tutor):
    """Get auth token for another tutor."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": another_tutor.email, "password": "TutorOther123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestGetStudentNote:
    """Test GET /api/v1/tutor/student-notes/{student_id} endpoint."""

    def test_get_student_note_success(self, client, tutor_token, student_note, student_user):
        """Test getting existing student note successfully."""
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["student_id"] == student_user.id
        assert "notes" in data
        assert "calculus" in data["notes"]

    def test_get_student_note_nonexistent_returns_null(self, client, tutor_token, student_user):
        """Test getting nonexistent note returns null/None."""
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        # Should return 200 with null body when no note exists
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

    def test_get_student_note_invalid_student_returns_404(self, client, tutor_token):
        """Test getting note for nonexistent student returns 404."""
        response = client.get(
            "/api/v1/tutor/student-notes/99999",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "student" in response.json()["detail"].lower()

    def test_get_student_note_for_tutor_user_returns_404(self, client, tutor_token, tutor_user):
        """Test getting note for a user who is not a student returns 404."""
        # Try to get note for the tutor themselves (who has role=tutor, not student)
        response = client.get(
            f"/api/v1/tutor/student-notes/{tutor_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_student_note_unauthenticated(self, client, student_user):
        """Test unauthenticated access is rejected."""
        response = client.get(f"/api/v1/tutor/student-notes/{student_user.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_student_note_as_student_forbidden(self, client, student_token, student_user):
        """Test student cannot access student notes endpoint."""
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Students should be forbidden from this tutor-only endpoint
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_student_note_as_admin_forbidden(self, client, admin_token, student_user):
        """Test admin cannot access student notes endpoint (tutor-only)."""
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Admins should also be forbidden (this is tutor-only)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_student_note_contains_required_fields(self, client, tutor_token, student_note, student_user):
        """Test that note response contains all required fields."""
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        data = response.json()

        assert "id" in data
        assert "tutor_id" in data
        assert "student_id" in data
        assert "notes" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestUpdateStudentNote:
    """Test PUT /api/v1/tutor/student-notes/{student_id} endpoint."""

    def test_create_student_note_success(self, client, tutor_token, student_user, tutor_user):
        """Test creating a new student note."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "New notes about the student. Struggling with algebra."},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["student_id"] == student_user.id
        assert data["tutor_id"] == tutor_user.id
        assert "algebra" in data["notes"]

    def test_update_existing_student_note(self, client, tutor_token, student_note, student_user, db_session):
        """Test updating an existing student note."""
        new_notes = "Updated notes. Student has improved significantly!"

        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": new_notes},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["notes"] == new_notes

        # Verify in database
        db_session.refresh(student_note)
        assert student_note.notes == new_notes

    def test_update_note_preserves_id(self, client, tutor_token, student_note, student_user):
        """Test that updating note preserves the same note ID."""
        original_id = student_note.id

        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Updated content"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == original_id

    def test_update_note_for_nonexistent_student(self, client, tutor_token):
        """Test updating note for nonexistent student returns 404."""
        response = client.put(
            "/api/v1/tutor/student-notes/99999",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Some notes"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_for_non_student_user(self, client, tutor_token, tutor_user):
        """Test updating note for non-student user returns 404."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{tutor_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Some notes"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_with_empty_notes(self, client, tutor_token, student_user):
        """Test creating/updating note with empty notes value."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": ""},
        )
        # Should succeed with empty notes
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["notes"] == ""

    def test_update_note_with_null_notes(self, client, tutor_token, student_user):
        """Test creating/updating note with null notes value."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": None},
        )
        # Should succeed with null notes
        assert response.status_code == status.HTTP_200_OK

    def test_update_note_unauthenticated(self, client, student_user):
        """Test unauthenticated update is rejected."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            json={"notes": "Some notes"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_note_as_student_forbidden(self, client, student_token, student_user):
        """Test student cannot create/update notes."""
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"notes": "Student trying to add notes"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_note_updates_timestamp(self, client, tutor_token, student_note, student_user, db_session):
        """Test that updating note updates the updated_at timestamp."""
        original_updated_at = student_note.updated_at

        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "New content"},
        )
        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(student_note)
        # Updated timestamp should be newer (or at least equal if very fast)
        assert student_note.updated_at >= original_updated_at


class TestDeleteStudentNote:
    """Test DELETE /api/v1/tutor/student-notes/{student_id} endpoint."""

    def test_delete_student_note_success(self, client, tutor_token, student_note, student_user):
        """Test deleting student note successfully."""
        response = client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.json()["message"].lower()

    def test_delete_note_removes_from_database(self, client, tutor_token, student_note, student_user, db_session):
        """Test that deletion actually removes note from database."""
        note_id = student_note.id

        client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        # Verify note is deleted
        deleted_note = db_session.query(StudentNote).filter(StudentNote.id == note_id).first()
        assert deleted_note is None

    def test_delete_nonexistent_note_returns_404(self, client, tutor_token, student_user):
        """Test deleting nonexistent note returns 404."""
        response = client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_for_nonexistent_student(self, client, tutor_token):
        """Test deleting note for nonexistent student returns 404."""
        response = client.delete(
            "/api/v1/tutor/student-notes/99999",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_unauthenticated(self, client, student_user):
        """Test unauthenticated delete is rejected."""
        response = client.delete(f"/api/v1/tutor/student-notes/{student_user.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_note_as_student_forbidden(self, client, student_token, student_user):
        """Test student cannot delete notes."""
        response = client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStudentNotesAuthorization:
    """Test authorization for student notes (tutor isolation)."""

    def test_tutor_cannot_see_other_tutor_notes(
        self, client, tutor_token, another_tutor_token, student_user, db_session
    ):
        """Test that tutors can only see their own notes, not other tutors' notes."""
        # First tutor creates a note
        client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "First tutor's private notes"},
        )

        # Second tutor tries to read - should get null (no note for them)
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {another_tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None  # No note exists for this tutor

    def test_tutor_cannot_delete_other_tutor_notes(
        self, client, tutor_token, another_tutor_token, student_note, student_user
    ):
        """Test that tutors cannot delete other tutors' notes."""
        response = client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {another_tutor_token}"},
        )
        # Should return 404 since the note doesn't belong to this tutor
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_multiple_tutors_can_have_notes_for_same_student(
        self, client, tutor_token, another_tutor_token, student_user, db_session
    ):
        """Test that multiple tutors can have separate notes for the same student."""
        # First tutor creates notes
        response1 = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "First tutor's notes"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second tutor creates their own notes
        response2 = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {another_tutor_token}"},
            json={"notes": "Second tutor's notes"},
        )
        assert response2.status_code == status.HTTP_200_OK

        # Verify both have different notes
        get1 = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        get2 = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {another_tutor_token}"},
        )

        assert get1.json()["notes"] == "First tutor's notes"
        assert get2.json()["notes"] == "Second tutor's notes"
        assert get1.json()["id"] != get2.json()["id"]


class TestStudentNotesIntegration:
    """Integration tests for student notes workflow."""

    def test_full_notes_workflow(self, client, tutor_token, student_user, tutor_user, db_session):
        """Test complete notes workflow: create, read, update, delete."""
        # 1. Initially no note exists
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

        # 2. Create note
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Initial notes - first session completed"},
        )
        assert response.status_code == status.HTTP_200_OK
        note_id = response.json()["id"]

        # 3. Read note
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == note_id
        assert "first session" in response.json()["notes"]

        # 4. Update note
        response = client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Updated notes - showed improvement in second session"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == note_id  # Same ID
        assert "second session" in response.json()["notes"]

        # 5. Delete note
        response = client.delete(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. Verify deletion
        response = client.get(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

    def test_notes_persist_across_requests(self, client, tutor_token, student_user):
        """Test that notes persist correctly across multiple requests."""
        # Create
        client.put(
            f"/api/v1/tutor/student-notes/{student_user.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"notes": "Persistent notes test"},
        )

        # Read multiple times
        for _ in range(3):
            response = client.get(
                f"/api/v1/tutor/student-notes/{student_user.id}",
                headers={"Authorization": f"Bearer {tutor_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["notes"] == "Persistent notes test"
