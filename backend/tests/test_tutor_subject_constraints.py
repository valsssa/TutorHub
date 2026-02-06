"""Tests for TutorSubject constraints."""

from models.tutors import TutorSubject


def test_proficiency_level_uses_uppercase():
    """Verify proficiency_level constraint uses UPPERCASE values to match database schema."""
    constraints = TutorSubject.__table__.constraints
    check_constraints = [c for c in constraints if hasattr(c, "sqltext")]

    proficiency_constraint = next(
        (c for c in check_constraints if "proficiency_level" in str(c.sqltext)), None
    )
    assert proficiency_constraint is not None, "proficiency_level constraint not found"

    # Should use UPPERCASE values (matching database/migrations/001_baseline_schema.sql)
    sqltext = str(proficiency_constraint.sqltext)
    assert "'NATIVE'" in sqltext, f"Expected 'NATIVE' in constraint, got: {sqltext}"
    assert "'C2'" in sqltext, f"Expected 'C2' in constraint, got: {sqltext}"
    assert "'C1'" in sqltext, f"Expected 'C1' in constraint, got: {sqltext}"
    assert "'B2'" in sqltext, f"Expected 'B2' in constraint, got: {sqltext}"
    assert "'B1'" in sqltext, f"Expected 'B1' in constraint, got: {sqltext}"
    assert "'A2'" in sqltext, f"Expected 'A2' in constraint, got: {sqltext}"
    assert "'A1'" in sqltext, f"Expected 'A1' in constraint, got: {sqltext}"

    # Should NOT have lowercase values
    assert "'native'" not in sqltext, f"Found lowercase 'native' in constraint: {sqltext}"
    assert "'c2'" not in sqltext, f"Found lowercase 'c2' in constraint: {sqltext}"
    assert "'c1'" not in sqltext, f"Found lowercase 'c1' in constraint: {sqltext}"
    assert "'b2'" not in sqltext, f"Found lowercase 'b2' in constraint: {sqltext}"
    assert "'b1'" not in sqltext, f"Found lowercase 'b1' in constraint: {sqltext}"
    assert "'a2'" not in sqltext, f"Found lowercase 'a2' in constraint: {sqltext}"
    assert "'a1'" not in sqltext, f"Found lowercase 'a1' in constraint: {sqltext}"


def test_proficiency_level_default_is_uppercase():
    """Verify proficiency_level column default is uppercase B2."""
    column = TutorSubject.__table__.c.proficiency_level
    assert column.default is not None, "proficiency_level should have a default"
    assert column.default.arg == "B2", f"Expected default 'B2', got '{column.default.arg}'"
