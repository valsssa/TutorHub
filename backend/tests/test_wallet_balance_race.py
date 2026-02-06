"""Tests for wallet balance race condition handling.

Verifies that wallet balance updates use atomic SQL operations
to prevent race conditions from concurrent transactions.
"""

from pathlib import Path


def test_wallet_balance_uses_atomic_update():
    """Verify wallet balance uses atomic SQL UPDATE in payments router.

    The wallet top-up handler should use atomic SQL UPDATE:
        db.execute(
            update(StudentProfile)
            .where(StudentProfile.id == profile_id)
            .values(credit_balance_cents=StudentProfile.credit_balance_cents + amount)
        )

    NOT the vulnerable read-modify-write pattern:
        profile.credit_balance_cents += amount
    """
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should use atomic update pattern with SQL expression
    has_atomic = (
        "StudentProfile.credit_balance_cents +" in source or
        "credit_balance_cents=StudentProfile.credit_balance_cents" in source or
        "execute(" in source  # Using raw SQL execute
    )
    assert has_atomic, "Wallet balance should use atomic update"


def test_wallet_balance_no_read_modify_write():
    """Verify no vulnerable read-modify-write pattern in critical paths.

    Patterns like:
        profile.credit_balance_cents += amount
        profile.credit_balance_cents -= amount

    Are vulnerable to race conditions when multiple concurrent requests
    update the same balance. These should not appear in production code.
    """
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should NOT have patterns like: profile.credit_balance_cents += amount
    # This indicates read-modify-write vulnerability
    vulnerable_pattern = (
        "credit_balance_cents += " in source or
        "credit_balance_cents -= " in source
    )
    assert not vulnerable_pattern, "Found vulnerable read-modify-write pattern"


def test_wallet_router_uses_db_execute():
    """Verify wallet router uses db.execute for balance updates.

    Direct db.execute() with SQLAlchemy Core update() is safer than
    ORM-level attribute assignment for concurrent operations.
    """
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should use db.execute for the atomic update
    assert "db.execute" in source, "Should use db.execute for atomic operations"
    assert "update(StudentProfile)" in source, "Should use update() for atomic balance changes"


def test_wallet_topup_handler_atomic():
    """Verify _handle_wallet_topup uses atomic update specifically.

    The webhook handler for wallet top-ups must use atomic SQL
    to prevent race conditions when multiple top-ups complete
    simultaneously.
    """
    import re

    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Find the _handle_wallet_topup function
    topup_match = re.search(
        r'async def _handle_wallet_topup\([^)]*\).*?(?=\nasync def |\ndef |\nclass |\Z)',
        source,
        re.DOTALL
    )

    assert topup_match, "_handle_wallet_topup function not found"
    topup_code = topup_match.group(0)

    # Should use db.execute with atomic update
    assert "db.execute" in topup_code, (
        "_handle_wallet_topup should use db.execute for atomic update"
    )

    # Should use SQL expression for balance increment
    assert "StudentProfile.credit_balance_cents +" in topup_code, (
        "_handle_wallet_topup should use SQL expression for atomic increment"
    )

    # Should NOT use vulnerable ORM assignment
    # But allow patterns like "student_profile.credit_balance_cents" in logging statements
    vulnerable_assignment = re.search(
        r'student_profile\.credit_balance_cents\s*[+\-]?=\s*[^=]',
        topup_code
    )
    assert not vulnerable_assignment, (
        "_handle_wallet_topup should not use ORM assignment for balance"
    )


def test_domain_entity_balance_methods_not_used_in_production():
    """Verify domain entity add_credits/deduct_credits not used in production routes.

    The StudentProfileEntity has add_credits() and deduct_credits() methods
    for domain logic, but these should NOT be used in production code paths
    that touch the database, as they create read-modify-write vulnerabilities.
    """
    # Check payments router
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Should not call entity methods for balance changes
    assert ".add_credits(" not in source, (
        "Payments router should not use entity.add_credits() - use atomic SQL instead"
    )
    assert ".deduct_credits(" not in source, (
        "Payments router should not use entity.deduct_credits() - use atomic SQL instead"
    )

    # Check wallet router
    wallet_path = Path(__file__).parent.parent / "modules" / "payments" / "wallet_router.py"
    wallet_source = wallet_path.read_text()

    assert ".add_credits(" not in wallet_source, (
        "Wallet router should not use entity.add_credits()"
    )
    assert ".deduct_credits(" not in wallet_source, (
        "Wallet router should not use entity.deduct_credits()"
    )


def test_atomic_update_includes_where_clause():
    """Verify atomic updates include proper WHERE clause.

    The atomic update must include a WHERE clause to target the specific
    profile being updated. Without it, all profiles would be updated.
    """
    import re

    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text()

    # Find update statements for credit_balance_cents
    update_pattern = re.search(
        r'update\(StudentProfile\).*?\.where\([^)]+\).*?\.values\([^)]*credit_balance_cents',
        source,
        re.DOTALL
    )

    assert update_pattern, (
        "Atomic update should have .where() clause before .values()"
    )


def test_balance_update_comment_documents_race_condition_protection():
    """Verify code includes comments documenting the race condition protection.

    Good code should document WHY atomic updates are used, not just WHAT is done.
    """
    router_path = Path(__file__).parent.parent / "modules" / "payments" / "router.py"
    source = router_path.read_text().lower()

    # Should have comments about race conditions or atomic updates
    has_documentation = (
        "race condition" in source or
        "atomic" in source or
        "concurrent" in source or
        "read-modify-write" in source
    )

    assert has_documentation, (
        "Code should document why atomic updates are used for balance changes"
    )
