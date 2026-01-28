"""
Centralized rate limiting configuration.

This module provides a shared rate limiter instance to be used across all API routers.
Using a single instance ensures consistent rate limiting behavior and configuration.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance
# Use this in all routers instead of creating separate instances
limiter = Limiter(key_func=get_remote_address)
