"""Tests for TutorProfile missing fields."""

from sqlalchemy import Boolean, Integer, Text, inspect

from models.tutors import (
    TutorAvailability,
    TutorCertification,
    TutorEducation,
    TutorProfile,
    TutorSubject,
)


class TestTutorProfileFields:
    """Tests for TutorProfile verification and badge fields."""

    def test_has_badges(self):
        """TutorProfile should have badges column (ARRAY(String))."""
        mapper = inspect(TutorProfile)
        columns = {c.key for c in mapper.columns}
        assert "badges" in columns

    def test_has_is_identity_verified(self):
        """TutorProfile should have is_identity_verified."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["is_identity_verified"]
        assert isinstance(col.type, Boolean)

    def test_has_is_education_verified(self):
        """TutorProfile should have is_education_verified."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["is_education_verified"]
        assert isinstance(col.type, Boolean)

    def test_has_is_background_checked(self):
        """TutorProfile should have is_background_checked."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["is_background_checked"]
        assert isinstance(col.type, Boolean)

    def test_has_verification_notes(self):
        """TutorProfile should have verification_notes."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["verification_notes"]
        assert isinstance(col.type, Text)

    def test_has_profile_completeness_score(self):
        """TutorProfile should have profile_completeness_score."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["profile_completeness_score"]
        assert isinstance(col.type, Integer)

    def test_has_last_completeness_check(self):
        """TutorProfile should have last_completeness_check."""
        mapper = inspect(TutorProfile)
        columns = {c.key for c in mapper.columns}
        assert "last_completeness_check" in columns

    def test_has_cancellation_strikes(self):
        """TutorProfile should have cancellation_strikes."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["cancellation_strikes"]
        assert isinstance(col.type, Integer)

    def test_has_trial_price_cents(self):
        """TutorProfile should have trial_price_cents."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["trial_price_cents"]
        assert isinstance(col.type, Integer)

    def test_has_payout_method(self):
        """TutorProfile should have payout_method (JSONB)."""
        mapper = inspect(TutorProfile)
        columns = {c.key for c in mapper.columns}
        assert "payout_method" in columns

    def test_has_teaching_philosophy(self):
        """TutorProfile should have teaching_philosophy."""
        mapper = inspect(TutorProfile)
        col = mapper.columns["teaching_philosophy"]
        assert isinstance(col.type, Text)


class TestTutorRelatedSoftDelete:
    """Tests for soft delete on tutor-related models."""

    def test_tutor_subject_has_soft_delete(self):
        """TutorSubject should have deleted_at and deleted_by."""
        mapper = inspect(TutorSubject)
        columns = {c.key for c in mapper.columns}
        assert "deleted_at" in columns
        assert "deleted_by" in columns

    def test_tutor_availability_has_soft_delete(self):
        """TutorAvailability should have deleted_at and deleted_by."""
        mapper = inspect(TutorAvailability)
        columns = {c.key for c in mapper.columns}
        assert "deleted_at" in columns
        assert "deleted_by" in columns

    def test_tutor_certification_has_soft_delete(self):
        """TutorCertification should have deleted_at and deleted_by."""
        mapper = inspect(TutorCertification)
        columns = {c.key for c in mapper.columns}
        assert "deleted_at" in columns
        assert "deleted_by" in columns

    def test_tutor_education_has_soft_delete(self):
        """TutorEducation should have deleted_at and deleted_by."""
        mapper = inspect(TutorEducation)
        columns = {c.key for c in mapper.columns}
        assert "deleted_at" in columns
        assert "deleted_by" in columns

    def test_tutor_profile_has_soft_delete(self):
        """TutorProfile should have deleted_at and deleted_by."""
        mapper = inspect(TutorProfile)
        columns = {c.key for c in mapper.columns}
        assert "deleted_at" in columns
        assert "deleted_by" in columns
