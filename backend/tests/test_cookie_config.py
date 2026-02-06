"""Tests for the cookie configuration module."""

from unittest.mock import MagicMock

from fastapi import Response

from core.cookie_config import (
    CookieConfig,
    clear_auth_cookies,
    get_cookie_config,
    set_access_token_cookie,
    set_csrf_cookie,
    set_refresh_token_cookie,
)


class TestCookieConfigDefaults:
    """Tests for CookieConfig default values."""

    def test_cookie_config_defaults(self):
        """Cookie config has secure defaults."""
        config = CookieConfig()

        assert config.access_token_name == "access_token"
        assert config.refresh_token_name == "refresh_token"
        assert config.csrf_token_name == "csrf_token"
        assert config.httponly is True
        assert config.samesite == "lax"  # Default when domain is None
        assert config.access_token_max_age == 900  # 15 minutes
        assert config.refresh_token_max_age == 604800  # 7 days

    def test_cookie_config_samesite_none_with_domain(self):
        """SameSite is 'none' when domain is configured for cross-subdomain auth."""
        config = CookieConfig(domain=".valsa.solutions")
        assert config.samesite == "none"

    def test_cookie_config_samesite_lax_without_domain(self):
        """SameSite is 'lax' when domain is None (same origin)."""
        config = CookieConfig(domain=None)
        assert config.samesite == "lax"

    def test_cookie_config_path_default(self):
        """Cookie path defaults to root."""
        config = CookieConfig()
        assert config.path == "/"


class TestCookieConfigSecure:
    """Tests for secure flag behavior."""

    def test_cookie_config_secure_in_production(self):
        """Secure flag enabled when not in development."""
        config = CookieConfig(environment="production")
        assert config.secure is True

    def test_cookie_config_secure_in_staging(self):
        """Secure flag enabled in staging."""
        config = CookieConfig(environment="staging")
        assert config.secure is True

    def test_cookie_config_not_secure_in_development(self):
        """Secure flag disabled in development."""
        config_dev = CookieConfig(environment="development")
        assert config_dev.secure is False


class TestCookieConfigDomain:
    """Tests for domain configuration."""

    def test_cookie_config_domain_setting(self):
        """Domain can be configured for subdomains."""
        config = CookieConfig(domain=".example.com")
        assert config.domain == ".example.com"

    def test_cookie_config_domain_none_default(self):
        """Domain defaults to None."""
        config_none = CookieConfig()
        assert config_none.domain is None


class TestGetCookieConfig:
    """Tests for get_cookie_config singleton."""

    def test_get_cookie_config_singleton(self):
        """get_cookie_config returns consistent instance."""
        # Clear the cache to ensure fresh state for this test
        get_cookie_config.cache_clear()

        config1 = get_cookie_config()
        config2 = get_cookie_config()
        assert config1 is config2

    def test_get_cookie_config_returns_cookie_config(self):
        """get_cookie_config returns CookieConfig instance."""
        get_cookie_config.cache_clear()
        config = get_cookie_config()
        assert isinstance(config, CookieConfig)


class TestSetAccessTokenCookie:
    """Tests for set_access_token_cookie helper."""

    def test_set_access_token_cookie_production(self):
        """Access token cookie is set with correct security attributes."""
        response = MagicMock(spec=Response)
        # No domain = same origin = samesite=lax
        config = CookieConfig(environment="production")
        set_access_token_cookie(response, "test_token", config)
        response.set_cookie.assert_called_once_with(
            key="access_token",
            value="test_token",
            max_age=900,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
            domain=None,
        )

    def test_set_access_token_cookie_cross_subdomain(self):
        """Access token cookie uses samesite=none for cross-subdomain auth."""
        response = MagicMock(spec=Response)
        # With domain = cross-subdomain = samesite=none
        config = CookieConfig(environment="production", domain=".valsa.solutions")
        set_access_token_cookie(response, "test_token", config)
        response.set_cookie.assert_called_once_with(
            key="access_token",
            value="test_token",
            max_age=900,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            domain=".valsa.solutions",
        )

    def test_set_access_token_cookie_development(self):
        """Access token cookie disables secure flag in development."""
        response = MagicMock(spec=Response)
        config = CookieConfig(environment="development")
        set_access_token_cookie(response, "dev_token", config)
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["secure"] is False
        assert call_kwargs["httponly"] is True

    def test_set_access_token_cookie_uses_default_config(self):
        """Access token cookie uses default config when none provided."""
        response = MagicMock(spec=Response)
        get_cookie_config.cache_clear()
        set_access_token_cookie(response, "token_value")
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["key"] == "access_token"


class TestSetRefreshTokenCookie:
    """Tests for set_refresh_token_cookie helper."""

    def test_set_refresh_token_cookie_production(self):
        """Refresh token cookie is set with restricted path."""
        response = MagicMock(spec=Response)
        # No domain = same origin = samesite=lax
        config = CookieConfig(environment="production")
        set_refresh_token_cookie(response, "refresh_test", config)
        response.set_cookie.assert_called_once_with(
            key="refresh_token",
            value="refresh_test",
            max_age=604800,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/api/v1/auth",
            domain=None,
        )

    def test_set_refresh_token_cookie_cross_subdomain(self):
        """Refresh token cookie uses samesite=none for cross-subdomain auth."""
        response = MagicMock(spec=Response)
        # With domain = cross-subdomain = samesite=none
        config = CookieConfig(environment="production", domain=".valsa.solutions")
        set_refresh_token_cookie(response, "refresh_test", config)
        response.set_cookie.assert_called_once_with(
            key="refresh_token",
            value="refresh_test",
            max_age=604800,
            httponly=True,
            secure=True,
            samesite="none",
            path="/api/v1/auth",
            domain=".valsa.solutions",
        )

    def test_set_refresh_token_cookie_restricted_path(self):
        """Refresh token path is restricted to auth endpoints only."""
        response = MagicMock(spec=Response)
        config = CookieConfig(environment="production")
        set_refresh_token_cookie(response, "refresh_value", config)
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["path"] == "/api/v1/auth"

    def test_set_refresh_token_cookie_uses_default_config(self):
        """Refresh token cookie uses default config when none provided."""
        response = MagicMock(spec=Response)
        get_cookie_config.cache_clear()
        set_refresh_token_cookie(response, "token_value")
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["key"] == "refresh_token"


class TestSetCsrfCookie:
    """Tests for set_csrf_cookie helper."""

    def test_set_csrf_cookie_production(self):
        """CSRF cookie is NOT httponly so JS can read it."""
        response = MagicMock(spec=Response)
        config = CookieConfig(environment="production")
        set_csrf_cookie(response, "csrf_value", config)
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["httponly"] is False
        assert call_kwargs["secure"] is True

    def test_set_csrf_cookie_same_lifetime_as_access(self):
        """CSRF cookie has same lifetime as access token."""
        response = MagicMock(spec=Response)
        config = CookieConfig(environment="production")
        set_csrf_cookie(response, "csrf_value", config)
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["max_age"] == config.access_token_max_age

    def test_set_csrf_cookie_uses_default_config(self):
        """CSRF cookie uses default config when none provided."""
        response = MagicMock(spec=Response)
        get_cookie_config.cache_clear()
        set_csrf_cookie(response, "csrf_value")
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["key"] == "csrf_token"


class TestClearAuthCookies:
    """Tests for clear_auth_cookies helper."""

    def test_clear_auth_cookies_deletes_all_three(self):
        """All three auth cookies are deleted on clear."""
        response = MagicMock(spec=Response)
        config = CookieConfig()
        clear_auth_cookies(response, config)
        assert response.delete_cookie.call_count == 3
        deleted_cookies = [
            call[1]["key"] for call in response.delete_cookie.call_args_list
        ]
        assert "access_token" in deleted_cookies
        assert "refresh_token" in deleted_cookies
        assert "csrf_token" in deleted_cookies

    def test_clear_auth_cookies_correct_paths(self):
        """Each cookie is deleted with its correct path."""
        response = MagicMock(spec=Response)
        config = CookieConfig()
        clear_auth_cookies(response, config)

        calls_by_key = {
            call[1]["key"]: call[1] for call in response.delete_cookie.call_args_list
        }
        assert calls_by_key["access_token"]["path"] == "/"
        assert calls_by_key["refresh_token"]["path"] == "/api/v1/auth"
        assert calls_by_key["csrf_token"]["path"] == "/"

    def test_clear_auth_cookies_uses_default_config(self):
        """Clear cookies uses default config when none provided."""
        response = MagicMock(spec=Response)
        get_cookie_config.cache_clear()
        clear_auth_cookies(response)
        assert response.delete_cookie.call_count == 3
