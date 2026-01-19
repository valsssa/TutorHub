"""Tests for tutor listing and profile endpoints."""

from decimal import Decimal

from fastapi import status


class TestTutorListing:
    """Test tutor listing endpoints."""

    def test_list_tutors_returns_only_approved(
        self, client, test_db_session, student_token
    ):
        """Test that only approved tutors are returned."""
        from models import TutorProfile, User

        # Create tutors with different statuses
        tutor_approved = User(
            email="approved@test.com", hashed_password="hash", role="tutor"
        )
        tutor_pending = User(
            email="pending@test.com", hashed_password="hash", role="tutor"
        )
        tutor_rejected = User(
            email="rejected@test.com", hashed_password="hash", role="tutor"
        )
        test_db_session.add_all([tutor_approved, tutor_pending, tutor_rejected])
        test_db_session.commit()

        # Create profiles
        profile_approved = TutorProfile(
            user_id=tutor_approved.id,
            title="Approved Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
        )
        profile_pending = TutorProfile(
            user_id=tutor_pending.id,
            title="Pending Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=False,
            profile_status="pending_approval",
        )
        profile_rejected = TutorProfile(
            user_id=tutor_rejected.id,
            title="Rejected Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=False,
            profile_status="rejected",
        )
        test_db_session.add_all([profile_approved, profile_pending, profile_rejected])
        test_db_session.commit()

        # List tutors as student
        response = client.get(
            "/api/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

        # Only approved tutor should be visible
        titles = [tutor["title"] for tutor in data["items"]]
        assert "Approved Tutor" in titles
        assert "Pending Tutor" not in titles
        assert "Rejected Tutor" not in titles

    def test_list_tutors_pagination(self, client, test_db_session, student_token):
        """Test tutor listing pagination."""
        from models import TutorProfile, User

        # Create multiple approved tutors
        for i in range(25):
            user = User(
                email=f"tutor{i}@test.com", hashed_password="hash", role="tutor"
            )
            test_db_session.add(user)
            test_db_session.commit()

            profile = TutorProfile(
                user_id=user.id,
                title=f"Tutor {i}",
                hourly_rate=Decimal("50.00"),
                is_approved=True,
                profile_status="approved",
            )
            test_db_session.add(profile)
        test_db_session.commit()

        # Test page 1
        response = client.get(
            "/api/tutors?page=1&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["pages"] >= 3  # At least 25 tutors / 10 per page

        # Test page 2
        response = client.get(
            "/api/tutors?page=2&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    def test_list_tutors_filter_by_subject(
        self, client, test_db_session, student_token
    ):
        """Test filtering tutors by subject."""
        from models import Subject, TutorProfile, TutorSubject, User

        # Create subjects
        math = Subject(name="Mathematics", is_active=True)
        english = Subject(name="English", is_active=True)
        test_db_session.add_all([math, english])
        test_db_session.commit()

        # Create tutors
        tutor1 = User(email="math_tutor@test.com", hashed_password="hash", role="tutor")
        tutor2 = User(
            email="english_tutor@test.com", hashed_password="hash", role="tutor"
        )
        test_db_session.add_all([tutor1, tutor2])
        test_db_session.commit()

        profile1 = TutorProfile(
            user_id=tutor1.id,
            title="Math Tutor",
            hourly_rate=Decimal("60.00"),
            is_approved=True,
            profile_status="approved",
        )
        profile2 = TutorProfile(
            user_id=tutor2.id,
            title="English Tutor",
            hourly_rate=Decimal("55.00"),
            is_approved=True,
            profile_status="approved",
        )
        test_db_session.add_all([profile1, profile2])
        test_db_session.commit()

        # Add subjects to tutors
        tutor_subject1 = TutorSubject(
            tutor_profile_id=profile1.id,
            subject_id=math.id,
            proficiency_level="C2",
            years_experience=5,
        )
        tutor_subject2 = TutorSubject(
            tutor_profile_id=profile2.id,
            subject_id=english.id,
            proficiency_level="Native",
            years_experience=10,
        )
        test_db_session.add_all([tutor_subject1, tutor_subject2])
        test_db_session.commit()

        # Filter by math subject
        response = client.get(
            f"/api/tutors?subject_id={math.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [tutor["title"] for tutor in data["items"]]
        assert "Math Tutor" in titles
        assert "English Tutor" not in titles

    def test_list_tutors_filter_by_rate(self, client, test_db_session, student_token):
        """Test filtering tutors by hourly rate range."""
        from models import TutorProfile, User

        # Create tutors with different rates
        cheap_user = User(email="cheap@test.com", hashed_password="hash", role="tutor")
        medium_user = User(
            email="medium@test.com", hashed_password="hash", role="tutor"
        )
        expensive_user = User(
            email="expensive@test.com", hashed_password="hash", role="tutor"
        )
        test_db_session.add_all([cheap_user, medium_user, expensive_user])
        test_db_session.commit()

        cheap_profile = TutorProfile(
            user_id=cheap_user.id,
            title="Cheap Tutor",
            hourly_rate=Decimal("20.00"),
            is_approved=True,
            profile_status="approved",
        )
        medium_profile = TutorProfile(
            user_id=medium_user.id,
            title="Medium Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
        )
        expensive_profile = TutorProfile(
            user_id=expensive_user.id,
            title="Expensive Tutor",
            hourly_rate=Decimal("100.00"),
            is_approved=True,
            profile_status="approved",
        )
        test_db_session.add_all([cheap_profile, medium_profile, expensive_profile])
        test_db_session.commit()

        # Filter by rate range (40-60)
        response = client.get(
            "/api/tutors?min_rate=40&max_rate=60",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [tutor["title"] for tutor in data["items"]]
        assert "Medium Tutor" in titles
        assert "Cheap Tutor" not in titles
        assert "Expensive Tutor" not in titles

    def test_list_tutors_filter_by_rating(self, client, test_db_session, student_token):
        """Test filtering tutors by minimum rating."""
        from models import TutorProfile, User

        # Create tutors with different ratings
        low_rated = User(email="low@test.com", hashed_password="hash", role="tutor")
        high_rated = User(email="high@test.com", hashed_password="hash", role="tutor")
        test_db_session.add_all([low_rated, high_rated])
        test_db_session.commit()

        low_profile = TutorProfile(
            user_id=low_rated.id,
            title="Low Rated Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
            average_rating=Decimal("3.5"),
        )
        high_profile = TutorProfile(
            user_id=high_rated.id,
            title="High Rated Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
            average_rating=Decimal("4.8"),
        )
        test_db_session.add_all([low_profile, high_profile])
        test_db_session.commit()

        # Filter by min rating 4.0
        response = client.get(
            "/api/tutors?min_rating=4.0",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [tutor["title"] for tutor in data["items"]]
        assert "High Rated Tutor" in titles
        assert "Low Rated Tutor" not in titles

    def test_list_tutors_search_query(self, client, test_db_session, student_token):
        """Test searching tutors by query."""
        from models import TutorProfile, User

        # Create tutors
        math_tutor = User(email="math@test.com", hashed_password="hash", role="tutor")
        science_tutor = User(
            email="science@test.com", hashed_password="hash", role="tutor"
        )
        test_db_session.add_all([math_tutor, science_tutor])
        test_db_session.commit()

        math_profile = TutorProfile(
            user_id=math_tutor.id,
            title="Expert Mathematics Teacher",
            headline="Specialized in calculus",
            hourly_rate=Decimal("60.00"),
            is_approved=True,
            profile_status="approved",
        )
        science_profile = TutorProfile(
            user_id=science_tutor.id,
            title="Science Tutor",
            headline="Physics and Chemistry",
            hourly_rate=Decimal("55.00"),
            is_approved=True,
            profile_status="approved",
        )
        test_db_session.add_all([math_profile, science_profile])
        test_db_session.commit()

        # Search for "mathematics"
        response = client.get(
            "/api/tutors?search_query=mathematics",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [tutor["title"] for tutor in data["items"]]
        assert len(titles) >= 1
        assert any("Mathematics" in title for title in titles)

    def test_list_tutors_sorting(self, client, test_db_session, student_token):
        """Test sorting tutors by different criteria."""
        from models import TutorProfile, User

        # Create tutors
        users = []
        for i in range(3):
            user = User(
                email=f"tutor{i}@test.com", hashed_password="hash", role="tutor"
            )
            test_db_session.add(user)
            test_db_session.commit()
            users.append(user)

        # Different rates and ratings
        profile1 = TutorProfile(
            user_id=users[0].id,
            title="Tutor A",
            hourly_rate=Decimal("30.00"),
            average_rating=Decimal("4.5"),
            is_approved=True,
            profile_status="approved",
        )
        profile2 = TutorProfile(
            user_id=users[1].id,
            title="Tutor B",
            hourly_rate=Decimal("50.00"),
            average_rating=Decimal("4.8"),
            is_approved=True,
            profile_status="approved",
        )
        profile3 = TutorProfile(
            user_id=users[2].id,
            title="Tutor C",
            hourly_rate=Decimal("70.00"),
            average_rating=Decimal("4.2"),
            is_approved=True,
            profile_status="approved",
        )
        test_db_session.add_all([profile1, profile2, profile3])
        test_db_session.commit()

        # Test sort by rating (default - should show B first)
        response = client.get(
            "/api/tutors?sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Highest rated should be first
        assert data["items"][0]["title"] == "Tutor B"

        # Test sort by rate ascending
        response = client.get(
            "/api/tutors?sort_by=rate_asc",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Cheapest should be first
        assert data["items"][0]["title"] == "Tutor A"

    def test_list_tutors_requires_auth(self, client):
        """Test that tutor listing requires authentication."""
        response = client.get("/api/tutors")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_tutor_by_id(self, client, test_db_session, student_token):
        """Test getting single tutor profile by ID."""
        from models import TutorProfile, User

        tutor = User(email="get_tutor@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(tutor)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Test Tutor",
            headline="Great teacher",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.get(
            f"/api/tutors/{profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Tutor"
        assert data["headline"] == "Great teacher"

    def test_get_non_approved_tutor_returns_404(
        self, client, test_db_session, student_token
    ):
        """Test that non-approved tutors return 404."""
        from models import TutorProfile, User

        tutor = User(email="pending@test.com", hashed_password="hash", role="tutor")
        test_db_session.add(tutor)
        test_db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Pending Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=False,
            profile_status="pending_approval",
        )
        test_db_session.add(profile)
        test_db_session.commit()

        response = client.get(
            f"/api/tutors/{profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
