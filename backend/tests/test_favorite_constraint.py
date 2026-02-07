"""Tests for FavoriteTutor unique constraint."""

from sqlalchemy import inspect

from models.students import FavoriteTutor


def test_favorite_tutor_has_table_args():
    """FavoriteTutor should have __table_args__ defined."""
    assert hasattr(FavoriteTutor, "__table_args__")
    assert FavoriteTutor.__table_args__ is not None


def test_favorite_tutor_has_unique_index():
    """FavoriteTutor should have a partial unique index on (student_id, tutor_profile_id)."""
    table = FavoriteTutor.__table__
    indexes = list(table.indexes)
    unique_indexes = [idx for idx in indexes if idx.unique]
    assert len(unique_indexes) >= 1, "Should have at least one unique index"

    # Find the active favorites index
    active_idx = None
    for idx in unique_indexes:
        col_names = {c.name for c in idx.columns}
        if "student_id" in col_names and "tutor_profile_id" in col_names:
            active_idx = idx
            break

    assert active_idx is not None, "Should have unique index on (student_id, tutor_profile_id)"
    assert active_idx.unique is True


def test_favorite_tutor_unique_index_is_partial():
    """The unique index should be partial (WHERE deleted_at IS NULL)."""
    table = FavoriteTutor.__table__
    indexes = list(table.indexes)

    # Find the unique active index
    for idx in indexes:
        col_names = {c.name for c in idx.columns}
        if idx.unique and "student_id" in col_names and "tutor_profile_id" in col_names:
            # Check it has a WHERE clause (postgresql_where)
            assert idx.dialect_options.get("postgresql", {}).get("where") is not None or \
                hasattr(idx, "expressions"), \
                "Unique index should have a partial WHERE clause"
            break
    else:
        raise AssertionError("Unique index on (student_id, tutor_profile_id) not found")


def test_favorite_tutor_columns():
    """FavoriteTutor should have all expected columns."""
    mapper = inspect(FavoriteTutor)
    columns = {c.key for c in mapper.columns}
    expected = {"id", "student_id", "tutor_profile_id", "created_at", "deleted_at", "deleted_by"}
    assert expected.issubset(columns)
