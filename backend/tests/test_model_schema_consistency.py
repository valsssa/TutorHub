"""
Test suite to verify SQLAlchemy models match database schema.
Prevents runtime AttributeErrors and schema mismatches.
"""

import pytest
from sqlalchemy import inspect

from database import engine
from models import (
    Booking,
    TutorAvailability,
    TutorCertification,
    TutorPricingOption,
    TutorProfile,
    TutorSubject,
    User,
    UserProfile,
)


@pytest.fixture
def db_inspector():
    """Create database inspector."""
    return inspect(engine)


class TestTutorAvailabilitySchema:
    """Test TutorAvailability model matches database schema."""

    def test_table_exists(self, db_inspector):
        """Verify tutor_availabilities table exists."""
        assert "tutor_availabilities" in db_inspector.get_table_names()

    def test_required_columns_exist(self, db_inspector):
        """Verify all required columns exist in database."""
        columns = {col["name"]: col["type"] for col in db_inspector.get_columns("tutor_availabilities")}

        # Check required columns
        assert "id" in columns
        assert "tutor_profile_id" in columns, "Column should be tutor_profile_id, not tutor_id"
        assert "day_of_week" in columns, "Column should be day_of_week, not weekday"
        assert "start_time" in columns, "Column should be start_time (TIME), not start_minute"
        assert "end_time" in columns, "Column should be end_time (TIME), not end_minute"
        assert "is_recurring" in columns, "Missing is_recurring boolean column"
        assert "created_at" in columns

    def test_foreign_key_references_tutor_profiles(self, db_inspector):
        """Verify foreign key points to tutor_profiles, not users."""
        foreign_keys = db_inspector.get_foreign_keys("tutor_availabilities")

        # Should have exactly one FK to tutor_profiles
        tutor_profile_fks = [
            fk
            for fk in foreign_keys
            if fk["referred_table"] == "tutor_profiles" and "tutor_profile_id" in fk["constrained_columns"]
        ]

        assert len(tutor_profile_fks) == 1, (
            "tutor_availabilities should have FK to tutor_profiles(id) via tutor_profile_id column"
        )

    def test_model_has_correct_relationship(self):
        """Verify model has relationship to TutorProfile."""
        assert hasattr(TutorAvailability, "tutor_profile"), (
            "TutorAvailability model should have 'tutor_profile' relationship"
        )

    def test_tutor_profile_has_availabilities_relationship(self):
        """Verify TutorProfile has back_populates relationship."""
        assert hasattr(TutorProfile, "availabilities"), "TutorProfile model should have 'availabilities' relationship"

    def test_model_columns_match_database(self, db_inspector):
        """Verify model column names match database."""
        model_columns = {col.name for col in TutorAvailability.__table__.columns}

        # Check key columns
        assert "tutor_profile_id" in model_columns
        assert "day_of_week" in model_columns
        assert "start_time" in model_columns
        assert "end_time" in model_columns
        assert "is_recurring" in model_columns

        # Should NOT have old column names
        assert "tutor_id" not in model_columns
        assert "weekday" not in model_columns
        assert "start_minute" not in model_columns
        assert "end_minute" not in model_columns


class TestTutorProfileRelationships:
    """Test TutorProfile has all required relationships."""

    def test_has_user_relationship(self):
        """Verify TutorProfile has user relationship."""
        assert hasattr(TutorProfile, "user")

    def test_has_subjects_relationship(self):
        """Verify TutorProfile has subjects relationship."""
        assert hasattr(TutorProfile, "subjects")

    def test_has_availabilities_relationship(self):
        """Verify TutorProfile has availabilities relationship."""
        assert hasattr(TutorProfile, "availabilities")

    def test_has_certifications_relationship(self):
        """Verify TutorProfile has certifications relationship."""
        assert hasattr(TutorProfile, "certifications")

    def test_has_educations_relationship(self):
        """Verify TutorProfile has educations relationship."""
        assert hasattr(TutorProfile, "educations")

    def test_has_pricing_options_relationship(self):
        """Verify TutorProfile has pricing_options relationship."""
        assert hasattr(TutorProfile, "pricing_options")

    def test_has_bookings_relationship(self):
        """Verify TutorProfile has bookings relationship."""
        assert hasattr(TutorProfile, "bookings")

    def test_has_reviews_relationship(self):
        """Verify TutorProfile has reviews relationship."""
        assert hasattr(TutorProfile, "reviews")


class TestDatabaseSchemaConsistency:
    """Test overall database-model consistency."""

    @pytest.mark.parametrize(
        "model,table_name",
        [
            (User, "users"),
            (UserProfile, "user_profiles"),
            (TutorProfile, "tutor_profiles"),
            (TutorSubject, "tutor_subjects"),
            (TutorAvailability, "tutor_availabilities"),
            (TutorCertification, "tutor_certifications"),
            (TutorPricingOption, "tutor_pricing_options"),
            (Booking, "bookings"),
        ],
    )
    def test_table_exists_for_model(self, db_inspector, model, table_name):
        """Verify database table exists for each model."""
        all_tables = db_inspector.get_table_names()
        assert table_name in all_tables, (
            f"Database table '{table_name}' not found for model {model.__name__}. "
            f"Available tables: {', '.join(sorted(all_tables))}"
        )

    def test_no_orphaned_relationships(self):
        """Verify all relationships have valid back_populates."""
        # Check TutorAvailability relationship
        availability_rel = TutorAvailability.__mapper__.relationships.get("tutor_profile")
        assert availability_rel is not None
        assert availability_rel.back_populates == "availabilities" or availability_rel.backref is not None

        # Check TutorProfile relationship
        profile_rel = TutorProfile.__mapper__.relationships.get("availabilities")
        assert profile_rel is not None
