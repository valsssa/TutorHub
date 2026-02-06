"""Tests to verify datetime usage in bookings module."""
from pathlib import Path


def test_no_utcnow_in_bookings_api():
    """Ensure datetime.utcnow() is not used in bookings API."""
    api_path = Path(__file__).parent.parent / "presentation" / "api.py"
    source = api_path.read_text()
    assert "utcnow()" not in source, (
        "Found datetime.utcnow() in bookings/presentation/api.py. "
        "Use core.datetime_utils.utc_now() instead."
    )


def test_no_utcnow_in_bookings_state_machine():
    """Ensure datetime.utcnow() is not used in state machine."""
    sm_path = Path(__file__).parent.parent / "domain" / "state_machine.py"
    source = sm_path.read_text()
    assert "utcnow()" not in source, (
        "Found datetime.utcnow() in bookings/domain/state_machine.py. "
        "Use core.datetime_utils.utc_now() instead."
    )
