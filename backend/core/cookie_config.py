"""Cookie configuration for HttpOnly token storage."""

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from fastapi import Response

from core.config import settings


@dataclass
class CookieConfig:
    """Configuration for authentication cookies.

    Provides secure defaults for HttpOnly cookie-based authentication.
    The Secure flag is automatically enabled in non-development environments.

    Cross-subdomain authentication:
        When frontend (e.g., edustream.valsa.solutions) and backend
        (e.g., api.valsa.solutions) are on different subdomains:
        1. The `domain` must be set to the parent domain (e.g., ".valsa.solutions")
        2. `SameSite` must be set to "none" for cross-origin requests with credentials
        3. `Secure` must be true (required when SameSite=None)

        Without proper configuration:
        - Cookies won't be sent on cross-origin fetch/XHR requests
        - CSRF token cookies set by the backend won't be readable by frontend JS
        - DELETE/POST/PUT requests will fail with 403 CSRF validation errors
    """

    # Cookie names
    access_token_name: str = "access_token"
    refresh_token_name: str = "refresh_token"
    csrf_token_name: str = "csrf_token"

    # Security settings
    httponly: bool = True
    path: str = "/"

    # TTL in seconds
    access_token_max_age: int = 900  # 15 minutes
    refresh_token_max_age: int = 604800  # 7 days

    # Environment-dependent
    environment: str = "development"
    domain: str | None = None  # Set to ".valsa.solutions" for cross-subdomain auth

    @property
    def secure(self) -> bool:
        """HTTPS-only cookies in non-development environments.

        Note: Secure=true is REQUIRED when SameSite=None.
        """
        return self.environment != "development"

    @property
    def samesite(self) -> Literal["lax", "strict", "none"]:
        """SameSite cookie attribute based on cross-subdomain configuration.

        When `domain` is set (cross-subdomain auth), cookies must use
        SameSite=None to be sent on cross-origin requests. This requires
        Secure=true (HTTPS), which is automatically enabled in production.

        In development (same origin), SameSite=Lax provides CSRF protection.
        """
        # Cross-subdomain auth requires SameSite=None
        if self.domain is not None:
            return "none"
        return "lax"


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


def set_access_token_cookie(
    response: "Response",
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set the access token as an HttpOnly secure cookie.

    Args:
        response: FastAPI Response object to set the cookie on.
        token: The JWT access token value.
        config: Optional CookieConfig; uses default if not provided.
    """
    if config is None:
        config = get_cookie_config()
    response.set_cookie(
        key=config.access_token_name,
        value=token,
        max_age=config.access_token_max_age,
        httponly=config.httponly,
        secure=config.secure,
        samesite=config.samesite,
        path=config.path,
        domain=config.domain,
    )


def set_refresh_token_cookie(
    response: "Response",
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set the refresh token as an HttpOnly secure cookie.

    The refresh token cookie is restricted to /api/v1/auth path
    to minimize exposure. It is only sent to auth endpoints.

    Args:
        response: FastAPI Response object to set the cookie on.
        token: The JWT refresh token value.
        config: Optional CookieConfig; uses default if not provided.
    """
    if config is None:
        config = get_cookie_config()
    response.set_cookie(
        key=config.refresh_token_name,
        value=token,
        max_age=config.refresh_token_max_age,
        httponly=config.httponly,
        secure=config.secure,
        samesite=config.samesite,
        path="/api/v1/auth",
        domain=config.domain,
    )


def set_csrf_cookie(
    response: "Response",
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set the CSRF token cookie for double-submit protection.

    Unlike the auth tokens, this cookie is NOT httponly because
    JavaScript must read it to include in request headers.

    Args:
        response: FastAPI Response object to set the cookie on.
        token: The CSRF token value.
        config: Optional CookieConfig; uses default if not provided.
    """
    if config is None:
        config = get_cookie_config()
    response.set_cookie(
        key=config.csrf_token_name,
        value=token,
        max_age=config.access_token_max_age,
        httponly=False,
        secure=config.secure,
        samesite=config.samesite,
        path=config.path,
        domain=config.domain,
    )


def clear_auth_cookies(
    response: "Response",
    config: CookieConfig | None = None,
) -> None:
    """Clear all authentication cookies on logout.

    Removes access_token, refresh_token, and csrf_token cookies.

    Args:
        response: FastAPI Response object to clear cookies on.
        config: Optional CookieConfig; uses default if not provided.
    """
    if config is None:
        config = get_cookie_config()
    response.delete_cookie(
        key=config.access_token_name,
        path=config.path,
        domain=config.domain,
    )
    response.delete_cookie(
        key=config.refresh_token_name,
        path="/api/v1/auth",
        domain=config.domain,
    )
    response.delete_cookie(
        key=config.csrf_token_name,
        path=config.path,
        domain=config.domain,
    )
