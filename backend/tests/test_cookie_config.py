"""Tests for the cookie configuration module."""

import pytest

from core.cookie_config import CookieConfig, get_cookie_config


class TestCookieConfigDefaults:
    """Tests for CookieConfig default values."""

    def test_cookie_config_defaults(self):
        """Cookie config has secure defaults."""
        config = CookieConfig()

        assert config.access_token_name == "access_token"
        assert config.refresh_token_name == "refresh_token"
        assert config.csrf_token_name == "csrf_token"
        assert config.httponly is True
        assert config.samesite == "lax"
        assert config.access_token_max_age == 900  # 15 minutes
        assert config.refresh_token_max_age == 604800  # 7 days

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
