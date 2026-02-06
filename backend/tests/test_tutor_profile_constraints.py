"""Tests for TutorProfile constraints."""
from models.tutors import TutorProfile


def test_profile_status_allows_archived():
    """Test that profile_status constraint includes 'archived' status."""
    constraints = TutorProfile.__table__.constraints
    check_constraints = [c for c in constraints if hasattr(c, 'sqltext')]

    status_constraint = next(
        (c for c in check_constraints if 'profile_status' in str(c.sqltext)), None
    )
    assert status_constraint is not None, "No profile_status constraint found"
    assert 'archived' in str(status_constraint.sqltext).lower(), (
        f"'archived' not found in profile_status constraint: {status_constraint.sqltext}"
    )
