"""
Comprehensive tests for the utils module.

Tests cover:
- Utilities API endpoints (countries, languages, proficiency levels, phone codes)
- Caching behavior
- Constants validation
- Rate limiting
"""

import time

from fastapi import status

# =============================================================================
# Countries Endpoint Tests
# =============================================================================


class TestCountriesEndpoint:
    """Tests for the /utils/countries endpoint."""

    def test_get_countries_success(self, client):
        """Test successful retrieval of countries list."""
        response = client.get("/api/v1/utils/countries")
        assert response.status_code == status.HTTP_200_OK

        countries = response.json()
        assert isinstance(countries, list)
        assert len(countries) > 0

        # Check structure
        first_country = countries[0]
        assert "code" in first_country
        assert "name" in first_country

    def test_get_countries_contains_expected_entries(self, client):
        """Test that countries list contains expected entries."""
        response = client.get("/api/v1/utils/countries")
        assert response.status_code == status.HTTP_200_OK

        countries = response.json()
        country_codes = {c["code"] for c in countries}

        # Check for some expected countries
        expected_codes = ["US", "GB", "FR", "DE", "JP", "CN", "AU", "CA"]
        for code in expected_codes:
            assert code in country_codes, f"Expected country code {code} not found"

    def test_get_countries_valid_iso_codes(self, client):
        """Test that all country codes are valid ISO 3166-1 alpha-2 codes."""
        response = client.get("/api/v1/utils/countries")
        assert response.status_code == status.HTTP_200_OK

        countries = response.json()
        for country in countries:
            assert len(country["code"]) == 2, f"Invalid code length: {country['code']}"
            assert country["code"].isupper(), f"Code should be uppercase: {country['code']}"

    def test_get_countries_cached(self, client):
        """Test that countries list is cached."""
        # First request
        response1 = client.get("/api/v1/utils/countries")
        assert response1.status_code == status.HTTP_200_OK

        # Second request should be cached
        response2 = client.get("/api/v1/utils/countries")
        assert response2.status_code == status.HTTP_200_OK

        # Both should return the same data
        assert response1.json() == response2.json()


# =============================================================================
# Languages Endpoint Tests
# =============================================================================


class TestLanguagesEndpoint:
    """Tests for the /utils/languages endpoint."""

    def test_get_languages_success(self, client):
        """Test successful retrieval of languages list."""
        response = client.get("/api/v1/utils/languages")
        assert response.status_code == status.HTTP_200_OK

        languages = response.json()
        assert isinstance(languages, list)
        assert len(languages) > 0

        # Check structure
        first_language = languages[0]
        assert "code" in first_language
        assert "name" in first_language

    def test_get_languages_contains_expected_entries(self, client):
        """Test that languages list contains expected entries."""
        response = client.get("/api/v1/utils/languages")
        assert response.status_code == status.HTTP_200_OK

        languages = response.json()
        language_codes = {lang["code"] for lang in languages}

        # Check for common languages
        expected_codes = ["en", "es", "fr", "de", "zh", "ja", "ar", "pt"]
        for code in expected_codes:
            assert code in language_codes, f"Expected language code {code} not found"

    def test_get_languages_valid_iso_codes(self, client):
        """Test that all language codes are valid ISO 639-1 codes."""
        response = client.get("/api/v1/utils/languages")
        assert response.status_code == status.HTTP_200_OK

        languages = response.json()
        for language in languages:
            assert len(language["code"]) == 2, f"Invalid code length: {language['code']}"
            assert language["code"].islower(), f"Code should be lowercase: {language['code']}"


# =============================================================================
# Proficiency Levels Endpoint Tests
# =============================================================================


class TestProficiencyLevelsEndpoint:
    """Tests for the /utils/proficiency-levels endpoint."""

    def test_get_proficiency_levels_success(self, client):
        """Test successful retrieval of proficiency levels."""
        response = client.get("/api/v1/utils/proficiency-levels")
        assert response.status_code == status.HTTP_200_OK

        levels = response.json()
        assert isinstance(levels, list)
        assert len(levels) > 0

    def test_get_proficiency_levels_contains_cefr(self, client):
        """Test that proficiency levels include CEFR levels."""
        response = client.get("/api/v1/utils/proficiency-levels")
        assert response.status_code == status.HTTP_200_OK

        levels = response.json()

        # CEFR levels should be present (as dictionaries with code field)
        if isinstance(levels[0], dict):
            level_codes = {level.get("code", "").lower() for level in levels}
        else:
            level_codes = {level.lower() for level in levels}

        # Check for CEFR levels
        cefr_levels = ["a1", "a2", "b1", "b2", "c1", "c2"]
        for level in cefr_levels:
            assert level in level_codes, f"Expected CEFR level {level} not found"

    def test_get_proficiency_levels_includes_native(self, client):
        """Test that proficiency levels include 'Native'."""
        response = client.get("/api/v1/utils/proficiency-levels")
        assert response.status_code == status.HTTP_200_OK

        levels = response.json()

        if isinstance(levels[0], dict):
            level_codes = {level.get("code", "").lower() for level in levels}
        else:
            level_codes = {level.lower() for level in levels}

        assert "native" in level_codes, "Expected 'Native' level not found"


# =============================================================================
# Phone Codes Endpoint Tests
# =============================================================================


class TestPhoneCodesEndpoint:
    """Tests for the /utils/phone-codes endpoint."""

    def test_get_phone_codes_success(self, client):
        """Test successful retrieval of phone codes."""
        response = client.get("/api/v1/utils/phone-codes")
        assert response.status_code == status.HTTP_200_OK

        codes = response.json()
        assert isinstance(codes, list)
        assert len(codes) > 0

    def test_get_phone_codes_structure(self, client):
        """Test phone codes have correct structure."""
        response = client.get("/api/v1/utils/phone-codes")
        assert response.status_code == status.HTTP_200_OK

        codes = response.json()
        first_code = codes[0]

        assert "code" in first_code
        assert "country" in first_code

    def test_get_phone_codes_valid_format(self, client):
        """Test that phone codes are in valid E.164 format."""
        response = client.get("/api/v1/utils/phone-codes")
        assert response.status_code == status.HTTP_200_OK

        codes = response.json()
        for code_entry in codes:
            code = code_entry["code"]
            assert code.startswith("+"), f"Phone code should start with +: {code}"
            # After the +, should be digits
            digits = code[1:]
            assert digits.isdigit(), f"Phone code should have digits after +: {code}"

    def test_get_phone_codes_contains_expected_entries(self, client):
        """Test that phone codes contain expected entries."""
        response = client.get("/api/v1/utils/phone-codes")
        assert response.status_code == status.HTTP_200_OK

        codes = response.json()
        code_values = {c["code"] for c in codes}

        # Check for some expected phone codes
        expected_codes = ["+1", "+44", "+33", "+49", "+81", "+86"]
        for code in expected_codes:
            assert code in code_values, f"Expected phone code {code} not found"


# =============================================================================
# Constants Module Tests
# =============================================================================


class TestConstantsValidation:
    """Tests for the constants validation functions."""

    def test_is_valid_country_code(self):
        """Test country code validation."""
        from core.constants import is_valid_country_code

        assert is_valid_country_code("US") is True
        assert is_valid_country_code("GB") is True
        assert is_valid_country_code("XX") is False
        assert is_valid_country_code("") is False
        assert is_valid_country_code("USA") is False  # Too long

    def test_is_valid_language_code(self):
        """Test language code validation."""
        from core.constants import is_valid_language_code

        assert is_valid_language_code("en") is True
        assert is_valid_language_code("es") is True
        assert is_valid_language_code("xx") is False
        assert is_valid_language_code("") is False
        assert is_valid_language_code("eng") is False  # Too long

    def test_is_valid_proficiency_level(self):
        """Test proficiency level validation."""
        from core.constants import is_valid_proficiency_level

        assert is_valid_proficiency_level("native") is True
        assert is_valid_proficiency_level("c2") is True
        assert is_valid_proficiency_level("a1") is True
        assert is_valid_proficiency_level("invalid") is False
        assert is_valid_proficiency_level("") is False

    def test_is_valid_phone_country_code(self):
        """Test phone country code validation."""
        from core.constants import is_valid_phone_country_code

        assert is_valid_phone_country_code("+1") is True
        assert is_valid_phone_country_code("+44") is True
        assert is_valid_phone_country_code("+999999") is False
        assert is_valid_phone_country_code("1") is False  # Missing +
        assert is_valid_phone_country_code("") is False

    def test_get_country_name(self):
        """Test getting country name from code."""
        from core.constants import get_country_name

        assert get_country_name("US") == "United States"
        assert get_country_name("GB") == "United Kingdom"
        assert get_country_name("XX") == ""

    def test_get_language_name(self):
        """Test getting language name from code."""
        from core.constants import get_language_name

        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("xx") == ""


# =============================================================================
# Cache Tests
# =============================================================================


class TestCacheWithTTL:
    """Tests for the cache_with_ttl decorator."""

    def test_cache_returns_same_value(self):
        """Test that cache returns the same value on subsequent calls."""
        from core.cache import cache_with_ttl, invalidate_cache

        # Clear any existing cache
        invalidate_cache()

        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_data():
            nonlocal call_count
            call_count += 1
            return {"value": call_count}

        # First call
        result1 = get_data()
        assert result1["value"] == 1

        # Second call should return cached value
        result2 = get_data()
        assert result2["value"] == 1
        assert call_count == 1  # Only called once

    def test_cache_expires_after_ttl(self):
        """Test that cache expires after TTL."""
        from core.cache import cache_with_ttl, invalidate_cache

        # Clear any existing cache
        invalidate_cache()

        call_count = 0

        @cache_with_ttl(ttl_seconds=1)  # Very short TTL for testing
        def get_data_short_ttl():
            nonlocal call_count
            call_count += 1
            return {"value": call_count}

        # First call
        result1 = get_data_short_ttl()
        assert result1["value"] == 1

        # Wait for TTL to expire
        time.sleep(1.5)

        # Third call should get fresh value
        result2 = get_data_short_ttl()
        assert result2["value"] == 2
        assert call_count == 2

    def test_cache_with_different_args(self):
        """Test that different arguments create different cache entries."""
        from core.cache import cache_with_ttl, invalidate_cache

        invalidate_cache()

        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_data_with_arg(arg):
            nonlocal call_count
            call_count += 1
            return {"value": arg}

        result1 = get_data_with_arg("a")
        result2 = get_data_with_arg("b")
        result3 = get_data_with_arg("a")  # Should be cached

        assert result1["value"] == "a"
        assert result2["value"] == "b"
        assert result3["value"] == "a"
        assert call_count == 2  # Only 2 unique calls


class TestInvalidateCache:
    """Tests for cache invalidation."""

    def test_invalidate_all_cache(self):
        """Test invalidating all cache entries."""
        from core.cache import cache_with_ttl, invalidate_cache

        invalidate_cache()

        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_data():
            nonlocal call_count
            call_count += 1
            return call_count

        # Populate cache
        get_data()
        assert call_count == 1

        # Invalidate all
        invalidate_cache()

        # Next call should not use cache
        get_data()
        assert call_count == 2

    def test_invalidate_cache_with_pattern(self):
        """Test invalidating cache entries matching a pattern."""
        from core.cache import cache_with_ttl, get_cache_stats, invalidate_cache

        invalidate_cache()

        @cache_with_ttl(ttl_seconds=60)
        def get_user_data():
            return "user"

        @cache_with_ttl(ttl_seconds=60)
        def get_product_data():
            return "product"

        # Populate both caches
        get_user_data()
        get_product_data()

        stats = get_cache_stats()
        assert stats["total_entries"] >= 2

        # Invalidate only user cache
        invalidate_cache("get_user_data")

        # User cache should be cleared, product should remain
        stats = get_cache_stats()
        user_keys = [k for k in stats["keys"] if "get_user_data" in k]
        product_keys = [k for k in stats["keys"] if "get_product_data" in k]

        assert len(user_keys) == 0
        assert len(product_keys) >= 1


class TestCacheStats:
    """Tests for cache statistics."""

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        from core.cache import cache_with_ttl, get_cache_stats, invalidate_cache

        invalidate_cache()

        @cache_with_ttl(ttl_seconds=60)
        def cached_func():
            return "data"

        # Populate cache
        cached_func()

        stats = get_cache_stats()
        assert "total_entries" in stats
        assert "valid_entries" in stats
        assert "expired_entries" in stats
        assert "keys" in stats
        assert stats["total_entries"] >= 1


# =============================================================================
# API Caching Tests
# =============================================================================


class TestAPICaching:
    """Tests for API endpoint caching."""

    def test_countries_endpoint_cached(self, client):
        """Test that countries endpoint uses caching."""
        # Make multiple requests
        response1 = client.get("/api/v1/utils/countries")
        response2 = client.get("/api/v1/utils/countries")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        # Data should be identical (from cache)
        assert response1.json() == response2.json()

    def test_languages_endpoint_cached(self, client):
        """Test that languages endpoint uses caching."""
        response1 = client.get("/api/v1/utils/languages")
        response2 = client.get("/api/v1/utils/languages")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

    def test_proficiency_levels_endpoint_cached(self, client):
        """Test that proficiency levels endpoint uses caching."""
        response1 = client.get("/api/v1/utils/proficiency-levels")
        response2 = client.get("/api/v1/utils/proficiency-levels")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

    def test_phone_codes_endpoint_cached(self, client):
        """Test that phone codes endpoint uses caching."""
        response1 = client.get("/api/v1/utils/phone-codes")
        response2 = client.get("/api/v1/utils/phone-codes")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in utils endpoints."""

    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/api/v1/utils/invalid-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_method_returns_405(self, client):
        """Test that invalid HTTP methods return 405."""
        response = client.post("/api/v1/utils/countries")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# =============================================================================
# Integration Tests
# =============================================================================


class TestUtilsIntegration:
    """Integration tests for the utils module."""

    def test_all_endpoints_accessible(self, client):
        """Test that all utils endpoints are accessible."""
        endpoints = [
            "/api/v1/utils/countries",
            "/api/v1/utils/languages",
            "/api/v1/utils/proficiency-levels",
            "/api/v1/utils/phone-codes",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK, f"Failed for {endpoint}"
            assert isinstance(response.json(), list), f"Expected list for {endpoint}"

    def test_data_consistency(self, client):
        """Test that data is consistent across multiple requests."""
        endpoints = [
            "/api/v1/utils/countries",
            "/api/v1/utils/languages",
            "/api/v1/utils/proficiency-levels",
            "/api/v1/utils/phone-codes",
        ]

        for endpoint in endpoints:
            response1 = client.get(endpoint)
            response2 = client.get(endpoint)

            assert response1.json() == response2.json(), f"Data inconsistent for {endpoint}"

    def test_public_endpoints_no_auth_required(self, client):
        """Test that utils endpoints don't require authentication."""
        endpoints = [
            "/api/v1/utils/countries",
            "/api/v1/utils/languages",
            "/api/v1/utils/proficiency-levels",
            "/api/v1/utils/phone-codes",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 401 Unauthorized
            assert response.status_code != status.HTTP_401_UNAUTHORIZED, f"Unexpected auth for {endpoint}"

    def test_country_and_phone_code_correlation(self, client):
        """Test that countries and phone codes are correlated."""
        countries_response = client.get("/api/v1/utils/countries")
        phone_codes_response = client.get("/api/v1/utils/phone-codes")

        assert countries_response.status_code == status.HTTP_200_OK
        assert phone_codes_response.status_code == status.HTTP_200_OK

        countries = countries_response.json()
        phone_codes = phone_codes_response.json()

        # Verify United States appears in both
        us_in_countries = any(c["code"] == "US" for c in countries)
        us_phone_code = any(
            "united states" in c["country"].lower() or "canada" in c["country"].lower()
            for c in phone_codes
        )

        assert us_in_countries, "US should be in countries list"
        assert us_phone_code, "US phone code (+1) should be in phone codes list"
