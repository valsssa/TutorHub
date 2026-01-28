"""
Backend-specific pytest configuration.

This file now imports from the consolidated root tests/conftest.py
to eliminate duplication. All fixtures are available from the root conftest.

DEPRECATED: This file is maintained for backward compatibility.
New tests should import fixtures from the root tests/conftest.py.
"""

import sys
from pathlib import Path

# Ensure root tests directory is in path
ROOT_DIR = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT_DIR / "tests"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# Import all fixtures from consolidated conftest
# This maintains backward compatibility for tests that import from backend/tests/conftest.py
from conftest import *  # noqa: F401,F403,E402

# Re-export commonly used fixtures for clarity
__all__ = [
    # Core fixtures
    "setup_database",
    "db_session",
    "db",
    "client",
    # User fixtures
    "admin_user",
    "tutor_user",
    "student_user",
    # Token fixtures (login-based)
    "admin_token",
    "tutor_token",
    "student_token",
    # Token fixtures (direct)
    "admin_token_direct",
    "tutor_token_direct",
    "student_token_direct",
    # Data fixtures
    "test_subject",
    "test_booking",
    # Legacy fixtures
    "test_student_token",
    "test_tutor_token",
    # Utility functions
    "create_test_user",
    "create_test_tutor_profile",
]
