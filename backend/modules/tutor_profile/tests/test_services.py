"""
Tutor Profile Service Tests

Tests for tutor profile creation, updates, approval workflow, and business logic.
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.modules.tutor_profile.application.services import TutorProfileService


@pytest.fixture
def tutor_profile_data():
    """Sample tutor profile data for testing"""
    return {
        "title": "Math Expert",
        "headline": "10+ years teaching experience",
        "bio": "Passionate about making math accessible",
        "hourly_rate": Decimal("50.00"),
        "experience_years": 10,
        "languages": ["en", "es"],
        "video_url": "https://youtube.com/watch?v=example",
    }


@pytest.fixture
def subject_data():
    """Sample subject assignment data"""
    return [
        {"subject_id": 1, "proficiency_level": "C2", "years_experience": 5},
        {"subject_id": 2, "proficiency_level": "B2", "years_experience": 3},
    ]


@pytest.fixture
def education_data():
    """Sample education data"""
    return [
        {
            "degree": "Bachelor of Science",
            "school": "MIT",
            "field_of_study": "Mathematics",
            "start_year": 2015,
            "end_year": 2019,
            "description": "Focus on applied mathematics",
        }
    ]


@pytest.fixture
def certification_data():
    """Sample certification data"""
    return [
        {
            "name": "Teaching Certificate",
            "issuing_organization": "State Board of Education",
            "issue_date": "2020-01-15",
            "credential_id": "CERT-12345",
        }
    ]


class TestTutorProfileCreation:
    """Test tutor profile creation"""

    def test_create_profile_success(self, db: Session, test_tutor_user, tutor_profile_data):
        """Test successful tutor profile creation"""
        # Given
        user_id = test_tutor_user.id

        # When
        profile = TutorProfileService.create_profile(db, user_id, tutor_profile_data)

        # Then
        assert profile.user_id == user_id
        assert profile.title == "Math Expert"
        assert profile.hourly_rate == Decimal("50.00")
        assert profile.experience_years == 10
        assert profile.profile_status == "incomplete"
        assert not profile.is_approved

    def test_create_profile_auto_initialization(self, db: Session, test_tutor_user_no_profile):
        """Test lazy profile creation on first access"""
        # Given
        user_id = test_tutor_user_no_profile.id

        # When
        profile = TutorProfileService.get_or_create_profile(db, user_id)

        # Then
        assert profile.user_id == user_id
        assert profile.profile_status == "incomplete"
        assert profile.hourly_rate is None  # Not yet set

    def test_create_profile_duplicate_error(self, db: Session, test_tutor_with_profile):
        """Test error when creating duplicate profile"""
        # Given
        user_id = test_tutor_with_profile.id

        # When/Then
        with pytest.raises(ValueError, match="Profile already exists"):
            TutorProfileService.create_profile(db, user_id, {})

    def test_create_profile_non_tutor_user_error(self, db: Session, test_student_user):
        """Test error when non-tutor tries to create profile"""
        # When/Then
        with pytest.raises(ValueError, match="User is not a tutor"):
            TutorProfileService.create_profile(db, test_student_user.id, {})

    def test_get_profile_by_user_non_tutor_error(self, db: Session, test_student_user):
        """Test error when non-tutor tries to access profile via get_profile_by_user"""
        # When/Then
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            TutorProfileService.get_profile_by_user(db, test_student_user.id)
        assert exc_info.value.status_code == 403
        assert "not 'tutor'" in str(exc_info.value.detail)


class TestTutorProfileUpdates:
    """Test profile update operations"""

    def test_update_about_section(self, db: Session, test_tutor_profile):
        """Test updating about/title/headline"""
        # Given
        updates = {"title": "Senior Math Tutor", "headline": "15 years of excellence", "bio": "Updated bio text"}

        # When
        updated = TutorProfileService.update_about(db, test_tutor_profile.id, updates)

        # Then
        assert updated.title == "Senior Math Tutor"
        assert updated.headline == "15 years of excellence"
        assert updated.bio == "Updated bio text"
        assert updated.updated_at > test_tutor_profile.updated_at

    def test_update_pricing(self, db: Session, test_tutor_profile):
        """Test updating hourly rate"""
        # Given
        new_rate = Decimal("75.00")

        # When
        updated = TutorProfileService.update_pricing(db, test_tutor_profile.id, {"hourly_rate": new_rate})

        # Then
        assert updated.hourly_rate == new_rate

    def test_update_pricing_invalid_rate(self, db: Session, test_tutor_profile):
        """Test error on invalid hourly rate"""
        # When/Then
        with pytest.raises(ValueError, match="Invalid hourly rate"):
            TutorProfileService.update_pricing(db, test_tutor_profile.id, {"hourly_rate": Decimal("-10.00")})

    def test_update_pricing_optimistic_locking(self, db: Session, test_tutor_profile):
        """Test optimistic locking prevents concurrent edits"""
        # Given
        new_rate = Decimal("75.00")
        original_version = test_tutor_profile.version

        # When/Then - Should succeed with correct version
        updated = TutorProfileService.update_pricing(
            db,
            test_tutor_profile.id,
            {"hourly_rate": new_rate},
            expected_version=original_version
        )
        assert updated.hourly_rate == new_rate
        assert updated.version == original_version + 1

        # When/Then - Should fail with stale version
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            TutorProfileService.update_pricing(
                db,
                test_tutor_profile.id,
                {"hourly_rate": Decimal("80.00")},
                expected_version=original_version  # Stale version
            )
        assert exc_info.value.status_code == 409
        assert "been modified by another request" in str(exc_info.value.detail)

    def test_update_description(self, db: Session, test_tutor_profile):
        """Test updating full description"""
        # Given
        new_description = "I have been teaching mathematics for over 15 years..."

        # When
        updated = TutorProfileService.update_description(db, test_tutor_profile.id, new_description)

        # Then
        assert updated.description == new_description

    def test_update_video_url(self, db: Session, test_tutor_profile):
        """Test updating intro video URL"""
        # Given
        video_url = "https://youtube.com/watch?v=newvideo"

        # When
        updated = TutorProfileService.update_video(db, test_tutor_profile.id, video_url)

        # Then
        assert updated.video_url == video_url

    def test_update_video_url_invalid(self, db: Session, test_tutor_profile):
        """Test error on invalid video URL"""
        # When/Then
        with pytest.raises(ValueError, match="Invalid video URL"):
            TutorProfileService.update_video(db, test_tutor_profile.id, "not-a-valid-url")


class TestTutorSubjects:
    """Test subject management"""

    def test_update_subjects(self, db: Session, test_tutor_profile, subject_data):
        """Test updating tutor subjects"""
        # When
        updated = TutorProfileService.update_subjects(db, test_tutor_profile.id, subject_data)

        # Then
        assert len(updated.subjects) == 2
        assert updated.subjects[0].subject_id == 1
        assert updated.subjects[0].proficiency_level == "C2"
        assert updated.subjects[0].years_experience == 5

    def test_update_subjects_replaces_existing(self, db: Session, test_tutor_profile_with_subjects):
        """Test that updating subjects replaces old ones"""
        # Given - profile has 2 subjects
        assert len(test_tutor_profile_with_subjects.subjects) == 2

        # When - update with 1 subject
        new_subjects = [{"subject_id": 3, "proficiency_level": "C1", "years_experience": 2}]
        updated = TutorProfileService.update_subjects(db, test_tutor_profile_with_subjects.id, new_subjects)

        # Then
        assert len(updated.subjects) == 1
        assert updated.subjects[0].subject_id == 3

    def test_update_subjects_invalid_proficiency(self, db: Session, test_tutor_profile):
        """Test error on invalid CEFR proficiency level"""
        # Given
        invalid_data = [{"subject_id": 1, "proficiency_level": "Z9", "years_experience": 5}]

        # When/Then
        with pytest.raises(ValueError, match="Invalid proficiency level"):
            TutorProfileService.update_subjects(db, test_tutor_profile.id, invalid_data)

    def test_update_subjects_nonexistent_subject(self, db: Session, test_tutor_profile):
        """Test error when subject doesn't exist"""
        # Given
        invalid_data = [{"subject_id": 99999, "proficiency_level": "C2", "years_experience": 5}]

        # When/Then
        with pytest.raises(ValueError, match="Subject not found"):
            TutorProfileService.update_subjects(db, test_tutor_profile.id, invalid_data)


class TestTutorEducation:
    """Test education management"""

    def test_add_education(self, db: Session, test_tutor_profile, education_data):
        """Test adding education entry"""
        # When
        updated = TutorProfileService.replace_education(db, test_tutor_profile.id, education_data)

        # Then
        assert len(updated.educations) == 1
        education = updated.educations[0]
        assert education.degree == "Bachelor of Science"
        assert education.school == "MIT"
        assert education.field_of_study == "Mathematics"

    def test_add_multiple_education_entries(self, db: Session, test_tutor_profile):
        """Test adding multiple education entries"""
        # Given
        educations = [
            {
                "degree": "Bachelor of Science",
                "school": "MIT",
                "field_of_study": "Mathematics",
                "start_year": 2015,
                "end_year": 2019,
            },
            {
                "degree": "Master of Science",
                "school": "Stanford",
                "field_of_study": "Applied Mathematics",
                "start_year": 2019,
                "end_year": 2021,
            },
        ]

        # When
        updated = TutorProfileService.replace_education(db, test_tutor_profile.id, educations)

        # Then
        assert len(updated.educations) == 2

    def test_education_year_validation(self, db: Session, test_tutor_profile):
        """Test validation that end_year >= start_year"""
        # Given
        invalid_education = [
            {
                "degree": "BS",
                "school": "University",
                "field_of_study": "Math",
                "start_year": 2020,
                "end_year": 2018,  # Invalid: before start year
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="End year must be after start year"):
            TutorProfileService.replace_education(db, test_tutor_profile.id, invalid_education)


class TestTutorCertifications:
    """Test certification management"""

    def test_add_certification(self, db: Session, test_tutor_profile, certification_data):
        """Test adding certification"""
        # When
        updated = TutorProfileService.replace_certifications(db, test_tutor_profile.id, certification_data)

        # Then
        assert len(updated.certifications) == 1
        cert = updated.certifications[0]
        assert cert.name == "Teaching Certificate"
        assert cert.issuing_organization == "State Board of Education"

    def test_certification_with_expiration(self, db: Session, test_tutor_profile):
        """Test certification with expiration date"""
        # Given
        cert_with_expiry = [
            {
                "name": "CPR Certification",
                "issuing_organization": "Red Cross",
                "issue_date": "2024-01-01",
                "expiration_date": "2026-01-01",
            }
        ]

        # When
        updated = TutorProfileService.replace_certifications(db, test_tutor_profile.id, cert_with_expiry)

        # Then
        cert = updated.certifications[0]
        assert cert.expiration_date is not None

    def test_certification_expiration_validation(self, db: Session, test_tutor_profile):
        """Test that expiration must be after issue date"""
        # Given
        invalid_cert = [
            {
                "name": "Certificate",
                "issuing_organization": "Org",
                "issue_date": "2025-01-01",
                "expiration_date": "2024-01-01",  # Before issue date
            }
        ]

        # When/Then
        with pytest.raises(ValueError, match="Expiration date must be after issue date"):
            TutorProfileService.replace_certifications(db, test_tutor_profile.id, invalid_cert)


class TestProfileCompletion:
    """Test profile completion calculation"""

    def test_calculate_completion_minimal_profile(self, db: Session, test_tutor_profile):
        """Test completion percentage for minimal profile"""
        # Given - only basic fields set
        test_tutor_profile.title = None
        test_tutor_profile.bio = None
        test_tutor_profile.hourly_rate = None
        db.commit()

        # When
        completion = TutorProfileService.calculate_completion_percentage(db, test_tutor_profile.id)

        # Then
        assert completion < 30  # Should be low

    def test_calculate_completion_partial_profile(self, db: Session, test_tutor_profile):
        """Test completion with some fields filled"""
        # Given
        test_tutor_profile.title = "Tutor"
        test_tutor_profile.bio = "Bio"
        test_tutor_profile.hourly_rate = Decimal("50.00")
        db.commit()

        # When
        completion = TutorProfileService.calculate_completion_percentage(db, test_tutor_profile.id)

        # Then
        assert 30 < completion < 70

    def test_calculate_completion_full_profile(self, db: Session, test_tutor_profile_complete):
        """Test completion for fully filled profile"""
        # Given - profile with all sections completed
        # When
        completion = TutorProfileService.calculate_completion_percentage(db, test_tutor_profile_complete.id)

        # Then
        assert completion >= 90


class TestProfileApproval:
    """Test admin approval workflow"""

    def test_submit_for_approval(self, db: Session, test_tutor_profile_ready):
        """Test submitting profile for admin review"""
        # Given - profile meets all requirements
        assert test_tutor_profile_ready.profile_status == "incomplete"

        # When
        result = TutorProfileService.submit_for_approval(db, test_tutor_profile_ready.id)

        # Then
        assert result.profile_status == "pending_approval"
        # Notification should be created for admin

    def test_submit_for_approval_incomplete_profile(self, db: Session, test_tutor_profile):
        """Test error when submitting incomplete profile"""
        # Given - profile not complete
        test_tutor_profile.hourly_rate = None  # Missing required field

        # When/Then
        with pytest.raises(ValueError, match="Profile not complete"):
            TutorProfileService.submit_for_approval(db, test_tutor_profile.id)

    def test_approve_profile(self, db: Session, test_admin_user, test_tutor_profile_pending):
        """Test admin approving tutor profile"""
        # Given
        assert test_tutor_profile_pending.profile_status == "pending_approval"

        # When
        approved = TutorProfileService.approve_profile(db, test_tutor_profile_pending.id, test_admin_user.id)

        # Then
        assert approved.is_approved
        assert approved.profile_status == "approved"
        assert approved.approved_by == test_admin_user.id
        assert approved.approved_at is not None
        # Audit log should be created
        # Notification sent to tutor

    def test_reject_profile(self, db: Session, test_admin_user, test_tutor_profile_pending):
        """Test admin rejecting tutor profile"""
        # Given
        reason = "Certifications not verified"

        # When
        rejected = TutorProfileService.reject_profile(db, test_tutor_profile_pending.id, test_admin_user.id, reason)

        # Then
        assert rejected.profile_status == "rejected"
        assert rejected.rejection_reason == reason
        assert not rejected.is_approved
        # Notification sent to tutor with reason

    def test_reject_profile_without_reason(self, db: Session, test_admin_user, test_tutor_profile_pending):
        """Test that rejection requires a reason"""
        # When/Then
        with pytest.raises(ValueError, match="Rejection reason required"):
            TutorProfileService.reject_profile(db, test_tutor_profile_pending.id, test_admin_user.id, "")

    def test_resubmit_after_rejection(self, db: Session, test_tutor_profile_rejected):
        """Test tutor can resubmit after fixing issues"""
        # Given - profile was rejected
        assert test_tutor_profile_rejected.profile_status == "rejected"

        # When - tutor fixes issues and resubmits
        test_tutor_profile_rejected.rejection_reason = None  # Clear old reason
        resubmitted = TutorProfileService.submit_for_approval(db, test_tutor_profile_rejected.id)

        # Then
        assert resubmitted.profile_status == "pending_approval"


class TestProfileVisibility:
    """Test profile visibility and search filtering"""

    def test_only_approved_profiles_in_public_search(self, db: Session):
        """Test that only approved profiles appear in search"""
        # Given - mix of profiles with different statuses
        # When
        public_profiles = TutorProfileService.get_public_profiles(db, filters={})

        # Then
        for profile in public_profiles:
            assert profile.is_approved
            assert profile.profile_status == "approved"

    def test_inactive_users_excluded_from_search(self, db: Session):
        """Test that inactive user profiles don't appear"""
        # Given - tutor user is inactive
        # When
        public_profiles = TutorProfileService.get_public_profiles(db, {})

        # Then
        for profile in public_profiles:
            assert profile.user.is_active


    def test_approve_profile(self, db: Session, test_admin_user, test_tutor_profile_pending):
        """Test admin approving tutor profile"""
        # When
        approved = TutorProfileService.approve_profile(
            db,
            test_tutor_profile_pending.id,
            test_admin_user.id
        )

        # Then
        assert approved.is_approved == True
        assert approved.profile_status == "approved"
        assert approved.approved_by == test_admin_user.id
        assert approved.approved_at is not None
        # Audit log created
        # Notification sent to tutor

    def test_reject_profile(self, db: Session, test_admin_user, test_tutor_profile_pending):
        """Test admin rejecting tutor profile"""
        # Given
        reason = "Certifications not verified"

        # When
        rejected = TutorProfileService.reject_profile(
            db,
            test_tutor_profile_pending.id,
            test_admin_user.id,
            reason
        )

        # Then
        assert rejected.profile_status == "rejected"
        assert rejected.rejection_reason == reason
        # Notification sent to tutor with reason


class TestTutorProfileService:
    """Test TutorProfileService business logic"""

    def test_create_profile_success(self, db, test_tutor_user):
        """Test successful tutor profile creation"""
        # Given
        profile_data = {
            "title": "Math Expert",
            "bio": "10 years experience",
            "hourly_rate": 50.00,
            "experience_years": 10
        }

        # When
        profile = TutorProfileService.create_profile(db, test_tutor_user.id, profile_data)

        # Then
        assert profile.user_id == test_tutor_user.id
        assert profile.title == "Math Expert"
        assert profile.hourly_rate == Decimal("50.00")
        assert profile.profile_status == "incomplete"

    def test_create_profile_duplicate_error(self, db, test_tutor_with_profile):
        """Test error when creating duplicate profile"""
        # When/Then
        with pytest.raises(ValueError, match="Profile already exists"):
            TutorProfileService.create_profile(db, test_tutor_with_profile.id, {})

    def test_update_profile_subjects(self, db, test_tutor_profile):
        """Test updating tutor subjects"""
        # Given
        subjects = [
            {"subject_id": 1, "proficiency_level": "C2", "years_experience": 5},
            {"subject_id": 2, "proficiency_level": "B2", "years_experience": 3}
        ]

        # When
        updated = TutorProfileService.update_subjects(db, test_tutor_profile.id, subjects)

        # Then
        assert len(updated.subjects) == 2
        assert updated.subjects[0].proficiency_level == "C2"

    def test_calculate_completion_percentage(self, db, test_tutor_profile):
        """Test profile completion calculation"""
        # Given - minimal profile
        assert test_tutor_profile.completion_percentage < 50

        # When - add more fields
        test_tutor_profile.title = "Expert"
        test_tutor_profile.bio = "Bio"
        test_tutor_profile.hourly_rate = 50.00
        test_tutor_profile.video_url = "https://youtube.com/..."
        db.commit()

        # Then
        completion = TutorProfileService.calculate_completion(db, test_tutor_profile.id)
        assert completion > 50

    def test_submit_for_approval(self, db, test_tutor_profile):
        """Test profile submission for admin review"""
        # Given - complete all required fields
        test_tutor_profile.title = "Expert"
        test_tutor_profile.bio = "Bio"
        test_tutor_profile.hourly_rate = 50.00
        test_tutor_profile.experience_years = 5
        # Add at least one subject
        db.add(TutorSubject(tutor_profile_id=test_tutor_profile.id, subject_id=1))
        db.commit()

        # When
        result = TutorProfileService.submit_for_approval(db, test_tutor_profile.id)

        # Then
        assert result.profile_status == "pending_approval"
        # Notification should be sent to admin


class TestAvailabilityService:
    """Test AvailabilityService business logic"""

    def test_create_recurring_availability(self, db, test_tutor_profile):
        """Test creating recurring weekly availability"""
        # Given
        slots = [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},  # Monday
            {"day_of_week": 3, "start_time": "10:00", "end_time": "16:00"}   # Wednesday
        ]

        # When
        result = AvailabilityService.set_availability(db, test_tutor_profile.id, slots)

        # Then
        assert len(result) == 2
        assert result[0].day_of_week == 1

    def test_availability_overlap_same_day(self, db, test_tutor_profile):
        """Test error on overlapping slots same day"""
        # Given - existing slot Mon 9am-5pm
        db.add(TutorAvailability(
            tutor_profile_id=test_tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        ))
        db.commit()

        # When - try to add Mon 3pm-7pm (overlap)
        with pytest.raises(ValueError, match="Overlapping availability"):
            AvailabilityService.add_slot(db, test_tutor_profile.id, {
                "day_of_week": 1,
                "start_time": "15:00",
                "end_time": "19:00"
            })

    def test_create_blackout_period(self, db, test_tutor_profile):
        """Test creating vacation/blackout period"""
        # Given
        blackout = {
            "start_time": "2025-12-20T00:00:00Z",
            "end_time": "2025-12-27T23:59:59Z",
            "reason": "Holiday vacation"
        }

        # When
        result = AvailabilityService.create_blackout(db, test_tutor_profile.id, blackout)

        # Then
        assert result.reason == "Holiday vacation"
        # Future bookings during this period should be blocked

    def test_get_available_slots(self, db, test_tutor_profile_with_availability):
        """Test retrieving available time slots for a date"""
        # Given - Mon 9am-5pm availability
        date = datetime(2025, 1, 6, tzinfo=timezone.utc)  # Monday

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile_with_availability.id,
            date,
            duration_minutes=60
        )

        # Then
        assert len(slots) > 0
        assert slots[0]["start_time"].hour == 9

    def test_available_slots_exclude_bookings(self, db, test_tutor_profile, test_booking):
        """Test that booked slots are excluded from available slots"""
        # Given - Mon 9am-5pm availability + booking 10am-11am
        date = test_booking.start_time.date()

        # When
        slots = AvailabilityService.get_available_slots(db, test_tutor_profile.id, date)

        # Then
        # 10am-11am slot should not be in available slots
        booked_time = test_booking.start_time.time()
        for slot in slots:
            assert slot["start_time"].time() != booked_time

    def test_available_slots_exclude_blackouts(self, db, test_tutor_profile, test_blackout):
        """Test that blackout periods exclude all slots"""
        # Given - Blackout Dec 20-27
        date = datetime(2025, 12, 23, tzinfo=timezone.utc)

        # When
        slots = AvailabilityService.get_available_slots(db, test_tutor_profile.id, date)

        # Then
        assert len(slots) == 0

    def test_replace_availability_with_timezone(self, db: Session, test_tutor_profile):
        """Test replacing availability with timezone handling"""
        # Given
        availability = [
            {
                "day_of_week": 1,  # Monday
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_recurring": True,
            }
        ]
        timezone = "America/New_York"

        # When
        updated = TutorProfileService.replace_availability(
            db, test_tutor_profile.user_id, availability, timezone
        )

        # Then
        assert len(updated.availabilities) == 1
        assert updated.availabilities[0].day_of_week == 1
        assert updated.availabilities[0].start_time.strftime("%H:%M:%S") == "09:00:00"
        assert updated.timezone == timezone

    def test_replace_availability_optimistic_locking(self, db: Session, test_tutor_profile):
        """Test optimistic locking prevents concurrent availability edits"""
        # Given
        availability = [{"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True}]
        original_version = test_tutor_profile.version

        # When/Then - Should succeed with correct version
        updated = TutorProfileService.replace_availability(
            db, test_tutor_profile.user_id, availability, expected_version=original_version
        )
        assert len(updated.availabilities) == 1
        assert updated.version == original_version + 1

        # When/Then - Should fail with stale version
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            TutorProfileService.replace_availability(
                db, test_tutor_profile.user_id, availability, expected_version=original_version
            )
        assert exc_info.value.status_code == 409
        assert "been modified by another request" in str(exc_info.value.detail)
