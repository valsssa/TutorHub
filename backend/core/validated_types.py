"""
Validated Pydantic types for automatic input sanitization.

These custom types can be used in Pydantic schemas to automatically
sanitize and validate input at the schema level, reducing boilerplate
in endpoint handlers.

Usage:
    from core.validated_types import SanitizedString, NonEmptyString

    class UserUpdateRequest(BaseModel):
        name: NonEmptyString
        bio: SanitizedString | None = None
"""

import html
import re
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator


def _sanitize_string(value: str | None) -> str | None:
    """Sanitize a string by escaping HTML and removing control characters."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace
    value = value.strip()

    # Remove null bytes
    value = value.replace("\x00", "")

    # Remove control characters except newline, tab, carriage return
    value = "".join(char for char in value if ord(char) >= 32 or char in "\n\t\r")

    # Escape HTML special characters
    value = html.escape(value, quote=False)

    return value


def _validate_non_empty(value: str | None) -> str:
    """Validate that a string is not empty after stripping."""
    if value is None:
        raise ValueError("Value cannot be None")

    value = value.strip()
    if not value:
        raise ValueError("Value cannot be empty")

    return value


def _sanitize_html_content(value: str | None) -> str | None:
    """Sanitize HTML content while preserving safe tags."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Remove null bytes
    value = value.replace("\x00", "")

    # Remove script tags and their content
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)

    # Remove on* event handlers
    value = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", value, flags=re.IGNORECASE)

    # Remove javascript: URLs
    value = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', value, flags=re.IGNORECASE)

    return value.strip()


def _normalize_email(value: str | None) -> str | None:
    """Normalize an email address."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Lowercase and strip
    value = value.lower().strip()

    # Basic validation
    if "@" not in value or len(value) > 254:
        raise ValueError("Invalid email format")

    return value


def _sanitize_url(value: str | None) -> str | None:
    """Sanitize a URL to prevent XSS."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    # Check for dangerous schemes
    dangerous_schemes = ["javascript:", "data:", "vbscript:", "file:"]
    value_lower = value.lower()

    for scheme in dangerous_schemes:
        if value_lower.startswith(scheme):
            raise ValueError(f"URL scheme not allowed: {scheme}")

    # Only allow http, https, and relative URLs
    if not (value.startswith("http://") or value.startswith("https://") or value.startswith("/")):
        raise ValueError("URL must be http, https, or relative path")

    return value


def _truncate_string(max_length: int):
    """Create a validator that truncates strings to max length."""

    def validator(value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > max_length:
            return value[:max_length]
        return value

    return validator


# ============================================================================
# Annotated Types for Pydantic Schemas
# ============================================================================


# Basic sanitized string - escapes HTML, removes control chars
SanitizedString = Annotated[str, BeforeValidator(_sanitize_string)]

# Non-empty string that's also sanitized
NonEmptyString = Annotated[str, BeforeValidator(_sanitize_string), AfterValidator(_validate_non_empty)]

# Non-empty string with max length
NonEmptyString100 = Annotated[
    str,
    BeforeValidator(_sanitize_string),
    AfterValidator(_validate_non_empty),
    BeforeValidator(_truncate_string(100)),
]

NonEmptyString255 = Annotated[
    str,
    BeforeValidator(_sanitize_string),
    AfterValidator(_validate_non_empty),
    BeforeValidator(_truncate_string(255)),
]

# Sanitized string with max lengths
SanitizedString100 = Annotated[str, BeforeValidator(_sanitize_string), BeforeValidator(_truncate_string(100))]
SanitizedString255 = Annotated[str, BeforeValidator(_sanitize_string), BeforeValidator(_truncate_string(255))]
SanitizedString1000 = Annotated[str, BeforeValidator(_sanitize_string), BeforeValidator(_truncate_string(1000))]
SanitizedString2000 = Annotated[str, BeforeValidator(_sanitize_string), BeforeValidator(_truncate_string(2000))]

# HTML content that's been sanitized (scripts removed)
SafeHtmlString = Annotated[str, BeforeValidator(_sanitize_html_content)]

# Normalized email address
NormalizedEmail = Annotated[str, BeforeValidator(_normalize_email)]

# Safe URL
SafeUrl = Annotated[str, BeforeValidator(_sanitize_url)]


# ============================================================================
# Optional versions (for fields that can be None)
# ============================================================================


SanitizedStringOptional = Annotated[str | None, BeforeValidator(_sanitize_string)]
NonEmptyStringOptional = Annotated[
    str | None,
    BeforeValidator(lambda v: _sanitize_string(v) if v else None),
    AfterValidator(lambda v: _validate_non_empty(v) if v else None),
]
SafeHtmlStringOptional = Annotated[str | None, BeforeValidator(_sanitize_html_content)]
NormalizedEmailOptional = Annotated[str | None, BeforeValidator(lambda v: _normalize_email(v) if v else None)]
SafeUrlOptional = Annotated[str | None, BeforeValidator(lambda v: _sanitize_url(v) if v else None)]
