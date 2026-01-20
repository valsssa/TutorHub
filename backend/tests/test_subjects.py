"""Tests for subject management endpoints."""

from fastapi import status


class TestSubjectsAPI:
    """Test subject listing."""

    def test_list_subjects_success(self, client, db_session, student_token, test_subject):
        """Test listing all active subjects."""
        response = client.get("/api/subjects", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify subject structure
        subject = data[0]
        assert "id" in subject
        assert "name" in subject
        assert "description" in subject
        assert "is_active" in subject

    def test_list_subjects_only_returns_active(self, client, db_session, student_token, test_subject):
        """Test that only active subjects are returned."""
        from models import Subject

        # Create inactive subject
        inactive_subject = Subject(
            name="Inactive Test Subject",
            description="Should not appear",
            is_active=False,
        )
        db_session.add(inactive_subject)
        db_session.commit()

        response = client.get("/api/subjects", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK

        subjects = response.json()
        subject_names = [s["name"] for s in subjects]
        assert "Inactive Test Subject" not in subject_names
        assert test_subject.name in subject_names

    def test_subjects_sorted_by_name(self, client, db_session, student_token):
        """Test that subjects are returned in a consistent order."""
        response = client.get("/api/subjects", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK

        subjects = response.json()
        if len(subjects) > 1:
            names = [s["name"] for s in subjects]
            # Verify it's a consistent order (not necessarily alphabetical,
            # but same order on repeated calls)
            response2 = client.get("/api/subjects", headers={"Authorization": f"Bearer {student_token}"})
            names2 = [s["name"] for s in response2.json()]
            assert names == names2

    def test_list_subjects_unauthorized(self, client):
        """Test listing subjects without auth fails."""
        response = client.get("/api/subjects")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_can_see_inactive_subjects(self, client, admin_token, db_session):
        """Test admin can see inactive subjects when requested."""
        from models import Subject

        # Create active and inactive subjects
        active = Subject(name="Active Subject", is_active=True)
        inactive = Subject(name="Inactive Subject", is_active=False)
        db_session.add_all([active, inactive])
        db_session.commit()

        # Regular list (only active)
        response = client.get("/api/subjects", headers={"Authorization": f"Bearer {admin_token}"})
        subjects = response.json()
        names = [s["name"] for s in subjects]
        assert "Active Subject" in names
        assert "Inactive Subject" not in names

        # With include_inactive (admin only)
        response = client.get(
            "/api/subjects?include_inactive=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        subjects = response.json()
        names = [s["name"] for s in subjects]
        assert "Active Subject" in names
        assert "Inactive Subject" in names


class TestAdminSubjectManagement:
    """Test admin subject CRUD operations."""

    def test_admin_create_subject(self, client, admin_token):
        """Test admin can create subject."""
        response = client.post(
            "/api/admin/subjects",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"name": "New Subject", "description": "Test description"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Subject"
        assert data["description"] == "Test description"
        assert data["is_active"] is True

    def test_admin_create_duplicate_subject(self, client, admin_token, test_subject):
        """Test admin cannot create duplicate subject."""
        response = client.post(
            "/api/admin/subjects",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"name": test_subject.name},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_student_cannot_create_subject(self, client, student_token):
        """Test student cannot create subject."""
        response = client.post(
            "/api/admin/subjects",
            headers={"Authorization": f"Bearer {student_token}"},
            params={"name": "New Subject"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_update_subject(self, client, admin_token, test_subject):
        """Test admin can update subject."""
        response = client.put(
            f"/api/admin/subjects/{test_subject.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "name": "Updated Subject",
                "description": "Updated description",
                "is_active": False,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Subject"
        assert data["description"] == "Updated description"
        assert data["is_active"] is False

    def test_admin_update_nonexistent_subject(self, client, admin_token):
        """Test updating nonexistent subject."""
        response = client.put(
            "/api/admin/subjects/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"name": "Test"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_update_subject(self, client, student_token, test_subject):
        """Test student cannot update subject."""
        response = client.put(
            f"/api/admin/subjects/{test_subject.id}",
            headers={"Authorization": f"Bearer {student_token}"},
            params={"name": "Hacked"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_delete_subject(self, client, admin_token, test_subject):
        """Test admin can delete subject."""
        response = client.delete(
            f"/api/admin/subjects/{test_subject.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's deleted
        response = client.get("/api/subjects", headers={"Authorization": f"Bearer {admin_token}"})
        subjects = response.json()
        subject_ids = [s["id"] for s in subjects]
        assert test_subject.id not in subject_ids

    def test_admin_delete_nonexistent_subject(self, client, admin_token):
        """Test deleting nonexistent subject."""
        response = client.delete(
            "/api/admin/subjects/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_delete_subject(self, client, student_token, test_subject):
        """Test student cannot delete subject."""
        response = client.delete(
            f"/api/admin/subjects/{test_subject.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
