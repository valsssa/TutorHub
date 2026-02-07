"""Tests for StudentProfile fields including interests type."""

from sqlalchemy import inspect

from models.students import FavoriteTutor, StudentPackage, StudentProfile


def test_student_profile_has_interests():
    """StudentProfile should have interests column."""
    mapper = inspect(StudentProfile)
    columns = {c.key for c in mapper.columns}
    assert "interests" in columns


def test_student_profile_interests_is_array():
    """StudentProfile.interests should be an ARRAY type, not Text."""
    mapper = inspect(StudentProfile)
    col = mapper.columns["interests"]
    col_type_name = type(col.type).__name__
    assert col_type_name == "ARRAY", f"Expected ARRAY, got {col_type_name}"


def test_student_profile_interests_nullable():
    """StudentProfile.interests should be nullable."""
    mapper = inspect(StudentProfile)
    col = mapper.columns["interests"]
    assert col.nullable is True


def test_student_profile_has_soft_delete():
    """StudentProfile should have deleted_at and deleted_by."""
    mapper = inspect(StudentProfile)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_favorite_tutor_has_soft_delete():
    """FavoriteTutor should have deleted_at and deleted_by."""
    mapper = inspect(FavoriteTutor)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns


def test_student_package_has_soft_delete():
    """StudentPackage should have deleted_at and deleted_by."""
    mapper = inspect(StudentPackage)
    columns = {c.key for c in mapper.columns}
    assert "deleted_at" in columns
    assert "deleted_by" in columns
