"""CSRF protection utilities."""
import hmac
import secrets


def generate_csrf_token() -> str:
    """
    Generate a cryptographically secure CSRF token.

    Returns 64 character hex string (32 bytes of entropy).
    Uses secrets module for cryptographically secure random generation.
    """
    return secrets.token_hex(32)


def validate_csrf_token(cookie_token: str | None, header_token: str | None) -> bool:
    """
    Validate CSRF token using constant-time comparison.

    Implements the double-submit cookie pattern: compares token from cookie
    with token from header to prevent CSRF attacks.

    Args:
        cookie_token: Token from csrf_token cookie
        header_token: Token from X-CSRF-Token header

    Returns:
        True if tokens match, False otherwise

    Security Notes:
        - Uses hmac.compare_digest for constant-time comparison to prevent
          timing attacks
        - Returns False immediately for None or empty values
    """
    if not cookie_token or not header_token:
        return False
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(cookie_token, header_token)
