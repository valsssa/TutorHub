"""Input sanitization utilities to prevent XSS and injection attacks."""

import html
import re
from typing import Optional


def sanitize_html(text: Optional[str]) -> Optional[str]:
    """
    Sanitize HTML to prevent XSS attacks.

    Args:
        text: Input text that may contain HTML

    Returns:
        Sanitized text with HTML entities escaped
    """
    if not text:
        return text

    # Escape HTML special characters
    sanitized = html.escape(text, quote=True)

    return sanitized


def sanitize_filename(filename: Optional[str]) -> Optional[str]:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage
    """
    if not filename:
        return filename

    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Only allow alphanumeric, dash, underscore, and dot
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename


def sanitize_url(url: Optional[str]) -> Optional[str]:
    """
    Sanitize URL to prevent XSS via javascript: or data: schemes.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL or None if malicious
    """
    if not url:
        return url

    url = url.strip()

    # Check for dangerous schemes
    dangerous_schemes = ["javascript:", "data:", "vbscript:", "file:"]
    url_lower = url.lower()

    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return None

    # Only allow http, https, and relative URLs
    if not (
        url.startswith("http://") or url.startswith("https://") or url.startswith("/")
    ):
        return None

    return url


def sanitize_text_input(
    text: Optional[str], max_length: Optional[int] = None
) -> Optional[str]:
    """
    General text sanitization for user inputs.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return text

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove control characters except newline, tab, carriage return
    text = "".join(
        char for char in text if ord(char) >= 32 or char in ["\n", "\t", "\r"]
    )

    # Escape HTML
    text = html.escape(text, quote=False)

    # Enforce max length
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_phone_number(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number format (E.164).

    Args:
        phone: Phone number (with or without country code)
        country_code: Expected country code (e.g., "+1")

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False

    # Remove spaces, dashes, parentheses
    phone = re.sub(r"[\s\-\(\)]", "", phone)

    # Check if starts with + (E.164 format)
    if not phone.startswith("+"):
        return False

    # Check if country code matches
    if country_code and not phone.startswith(country_code):
        return False

    # E.164: + followed by 7-15 digits
    pattern = r"^\+\d{7,15}$"
    return bool(re.match(pattern, phone))


def sanitize_email(email: Optional[str]) -> Optional[str]:
    """
    Sanitize email address.

    Args:
        email: Email address

    Returns:
        Normalized email (lowercase, stripped)
    """
    if not email:
        return email

    # Normalize: lowercase and strip
    email = email.lower().strip()

    # Basic validation
    if "@" not in email or len(email) > 254:
        return None

    return email


def clean_search_query(query: Optional[str]) -> Optional[str]:
    """
    Clean search query to prevent SQL injection (extra safety).

    Args:
        query: Search query string

    Returns:
        Cleaned query
    """
    if not query:
        return query

    query = query.strip()

    # Remove SQL keywords (paranoid mode - ORM should handle this)
    dangerous_keywords = [
        "drop",
        "delete",
        "update",
        "insert",
        "select",
        "union",
        "exec",
        "execute",
        "script",
        "--",
        "/*",
        "*/",
        "xp_",
    ]

    query_lower = query.lower()
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            query = query.replace(keyword, "")

    # Limit length
    if len(query) > 200:
        query = query[:200]

    return query.strip()


def sanitize_string(
    text: Optional[str], max_length: Optional[int] = None, allow_html: bool = False
) -> Optional[str]:
    """
    General string sanitization for any text input.

    Args:
        text: Input text
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML (default: False)

    Returns:
        Sanitized string
    """
    if not text:
        return text

    # Strip whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace("\x00", "")

    # Escape HTML if not allowed
    if not allow_html:
        text = html.escape(text, quote=False)

    # Enforce max length
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_video_url(url: Optional[str]) -> bool:
    """
    Validate video URL (YouTube, Vimeo, Loom).

    Args:
        url: Video URL

    Returns:
        True if valid video hosting URL
    """
    if not url:
        return False

    url = url.strip().lower()

    # Allowed video platforms
    allowed_domains = [
        "youtube.com",
        "youtu.be",
        "vimeo.com",
        "loom.com",
        "wistia.com",
        "vidyard.com",
    ]

    # Check if URL contains allowed domain
    for domain in allowed_domains:
        if domain in url:
            return url.startswith("http://") or url.startswith("https://")

    return False
