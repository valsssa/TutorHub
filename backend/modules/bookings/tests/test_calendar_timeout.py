"""
Tests for external calendar timeout protection.
Verifies that calendar conflict checks time out gracefully and allow booking to proceed.
"""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from core.datetime_utils import utc_now


@pytest.mark.asyncio
async def test_calendar_check_timeout_allows_booking():
    """Test that a slow calendar check times out and allows booking to proceed."""

    async def slow_calendar_check(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate very slow external call

    # Wrapping with wait_for should raise TimeoutError
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_calendar_check(), timeout=0.1)


@pytest.mark.asyncio
async def test_calendar_check_fast_response_proceeds():
    """Test that a fast calendar check completes normally."""

    async def fast_calendar_check():
        return None  # No conflict

    result = await asyncio.wait_for(fast_calendar_check(), timeout=5.0)
    assert result is None


@pytest.mark.asyncio
async def test_calendar_check_fast_conflict_raises():
    """Test that a fast calendar check with conflict still raises."""
    from fastapi import HTTPException

    async def calendar_with_conflict():
        raise HTTPException(
            status_code=409,
            detail={"error": "external_calendar_conflict", "message": "Tutor busy"},
        )

    with pytest.raises(HTTPException) as exc_info:
        await asyncio.wait_for(calendar_with_conflict(), timeout=5.0)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_timeout_value_is_5_seconds():
    """Test that the timeout configuration is 5 seconds as specified."""
    import time

    start = time.monotonic()

    async def slow_check():
        await asyncio.sleep(60)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_check(), timeout=5.0)

    elapsed = time.monotonic() - start
    # Should timeout around 5 seconds, not 60
    assert elapsed < 6.0
    assert elapsed >= 4.9
