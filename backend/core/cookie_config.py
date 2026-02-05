"""Cookie configuration for HttpOnly token storage."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from core.config import settings


@dataclass
class CookieConfig:
    """Configuration for authentication cookies.

    Provides secure defaults for HttpOnly cookie-based authentication.
    The Secure flag is automatically enabled in non-development environments.
    """

    # Cookie names
    access_token_name: str = "access_token"
    refresh_token_name: str = "refresh_token"
    csrf_token_name: str = "csrf_token"

    # Security settings
    httponly: bool = True
    samesite: Literal["lax", "strict", "none"] = "lax"
    path: str = "/"

    # TTL in seconds
    access_token_max_age: int = 900  # 15 minutes
    refresh_token_max_age: int = 604800  # 7 days

    # Environment-dependent
    environment: str = "development"
    domain: str | None = None

    @property
    def secure(self) -> bool:
        """HTTPS-only cookies in non-development environments."""
        return self.environment != "development"


@lru_cache
def get_cookie_config() -> CookieConfig:
    """Get cookie configuration from settings.

    Returns a cached singleton instance of CookieConfig populated
    from application settings.
    """
    return CookieConfig(
        environment=getattr(settings, "ENVIRONMENT", "development"),
        domain=getattr(settings, "COOKIE_DOMAIN", None),
        access_token_max_age=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15) * 60,
    )
