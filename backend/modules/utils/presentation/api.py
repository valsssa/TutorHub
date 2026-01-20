"""Utilities API routes for constants and validators."""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.cache import cache_with_ttl
from core.constants import COUNTRIES, LANGUAGES, PHONE_COUNTRY_CODES, PROFICIENCY_LEVELS

router = APIRouter(prefix="/api/utils", tags=["utils"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@cache_with_ttl(ttl_seconds=3600)  # Cache for 1 hour (constants rarely change)
def _get_countries() -> list[dict[str, str]]:
    """Get countries list with caching."""
    return COUNTRIES


@cache_with_ttl(ttl_seconds=3600)
def _get_languages() -> list[dict[str, str]]:
    """Get languages list with caching."""
    return LANGUAGES


@cache_with_ttl(ttl_seconds=3600)
def _get_proficiency_levels() -> list[str]:
    """Get proficiency levels with caching."""
    return PROFICIENCY_LEVELS


@cache_with_ttl(ttl_seconds=3600)
def _get_phone_codes() -> list[dict[str, str]]:
    """Get phone country codes with caching."""
    return PHONE_COUNTRY_CODES


@router.get("/countries", response_model=list[dict[str, str]])
@limiter.limit("60/minute")
def get_countries(request: Request):
    """
    Get list of countries with ISO 3166-1 alpha-2 codes.

    Returns:
        List of countries with code and name
    """
    return _get_countries()


@router.get("/languages", response_model=list[dict[str, str]])
@limiter.limit("60/minute")
def get_languages(request: Request):
    """
    Get list of languages with ISO 639-1 codes.

    Returns:
        List of languages with code and name
    """
    return _get_languages()


@router.get("/proficiency-levels", response_model=list[str])
@limiter.limit("60/minute")
def get_proficiency_levels(request: Request):
    """
    Get list of language proficiency levels (CEFR framework + Native).

    Returns:
        List of proficiency levels from Native to A1
    """
    return _get_proficiency_levels()


@router.get("/phone-codes", response_model=list[dict[str, str]])
@limiter.limit("60/minute")
def get_phone_codes(request: Request):
    """
    Get list of phone country codes (ITU E.164 format).

    Returns:
        List of phone codes with country and code
    """
    return _get_phone_codes()
