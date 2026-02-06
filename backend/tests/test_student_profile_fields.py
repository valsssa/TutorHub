"""Tests for StudentProfile model fields."""

from sqlalchemy import inspect

from models.students import StudentProfile


def test_student_profile_has_interests():
    """Verify StudentProfile has interests field."""
    mapper = inspect(StudentProfile)
    columns = [c.key for c in mapper.columns]
    assert "interests" in columns


def test_student_profile_has_soft_delete():
    """Verify StudentProfile has soft delete fields."""
    mapper = inspect(StudentProfile)
    columns = [c.key for c in mapper.columns]
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_student_profile_has_all_expected_fields():
    """Verify StudentProfile has all expected fields from schema."""
    mapper = inspect(StudentProfile)
    columns = [c.key for c in mapper.columns]

    expected_fields = [
        "id",
        "user_id",
        "phone",
        "bio",
        "interests",
        "grade_level",
        "school_name",
        "learning_goals",
        "total_sessions",
        "credit_balance_cents",
        "preferred_language",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    ]

    for field in expected_fields:
        assert field in columns, f"Missing field: {field}"
