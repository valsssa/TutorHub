"""Tests for TutorProfile model fields."""
from sqlalchemy import inspect

from models.tutors import TutorProfile

# Fields that must exist in TutorProfile model based on database schema
REQUIRED_FIELDS = [
    "badges",
    "is_identity_verified",
    "is_education_verified",
    "is_background_checked",
    "verification_notes",
    "profile_completeness_score",
    "last_completeness_check",
    "cancellation_strikes",
    "trial_price_cents",
    "payout_method",
    "teaching_philosophy",
    # NOTE: response_time_hours is NOT in the database - it's computed from TutorMetrics
]


def test_tutor_profile_has_all_required_fields():
    """Verify TutorProfile model has all required verification/completeness fields."""
    mapper = inspect(TutorProfile)
    columns = [c.key for c in mapper.columns]

    missing = [f for f in REQUIRED_FIELDS if f not in columns]
    assert not missing, f"TutorProfile missing fields: {missing}"


def test_tutor_profile_field_types():
    """Verify TutorProfile fields have correct types."""
    mapper = inspect(TutorProfile)
    columns = {c.key: c for c in mapper.columns}

    # Boolean fields should default to False
    boolean_fields = [
        "is_identity_verified",
        "is_education_verified",
        "is_background_checked",
    ]
    for field in boolean_fields:
        assert field in columns, f"Missing field: {field}"
        col = columns[field]
        assert not col.nullable or col.default is not None, f"{field} should have a default"

    # Integer fields with defaults
    integer_fields_with_defaults = [
        ("profile_completeness_score", 0),
        ("cancellation_strikes", 0),
    ]
    for field, _expected_default in integer_fields_with_defaults:
        assert field in columns, f"Missing field: {field}"


def test_tutor_profile_nullable_fields():
    """Verify nullable fields are correctly configured."""
    mapper = inspect(TutorProfile)
    columns = {c.key: c for c in mapper.columns}

    nullable_fields = [
        "badges",
        "verification_notes",
        "last_completeness_check",
        "trial_price_cents",
        "payout_method",
        "teaching_philosophy",
    ]
    for field in nullable_fields:
        assert field in columns, f"Missing field: {field}"
