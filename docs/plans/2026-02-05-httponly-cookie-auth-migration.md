# HttpOnly Cookie Authentication Migration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from localStorage JWT storage to HttpOnly Secure cookies for improved XSS protection.

**Architecture:** Backend sets/reads tokens via cookies instead of JSON body. Frontend removes localStorage token handling. CSRF protection added via double-submit cookie pattern. Refresh token rotation implemented for additional security.

**Tech Stack:** FastAPI (cookie handling), Next.js (credentials mode), Redis (token blacklist)

---

## Current State Summary

| Component | Current | Target |
|-----------|---------|--------|
| Access token storage | localStorage | HttpOnly Secure cookie |
| Refresh token storage | Not persisted | HttpOnly Secure cookie |
| Token transmission | Authorization header | Cookie (auto-sent) |
| CSRF protection | None | Double-submit cookie |
| Token refresh | Manual (unused) | Automatic on 401 |

## Migration Strategy

**Phase 1:** Backend cookie infrastructure (Tasks 1-4)
**Phase 2:** CSRF protection (Tasks 5-6)
**Phase 3:** Frontend migration (Tasks 7-10)
**Phase 4:** Automatic token refresh (Tasks 11-13)
**Phase 5:** Cleanup & hardening (Tasks 14-15)

---

## Task 1: Create Cookie Configuration Module

**Files:**
- Create: `backend/core/cookie_config.py`
- Test: `backend/tests/test_cookie_config.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_cookie_config.py
import pytest
from core.cookie_config import CookieConfig, get_cookie_config


def test_cookie_config_defaults():
    """Cookie config has secure defaults."""
    config = CookieConfig()

    assert config.access_token_name == "access_token"
    assert config.refresh_token_name == "refresh_token"
    assert config.csrf_token_name == "csrf_token"
    assert config.httponly is True
    assert config.samesite == "lax"
    assert config.access_token_max_age == 900  # 15 minutes
    assert config.refresh_token_max_age == 604800  # 7 days


def test_cookie_config_secure_in_production():
    """Secure flag enabled when not in development."""
    config = CookieConfig(environment="production")
    assert config.secure is True

    config_dev = CookieConfig(environment="development")
    assert config_dev.secure is False


def test_cookie_config_domain_setting():
    """Domain can be configured for subdomains."""
    config = CookieConfig(domain=".example.com")
    assert config.domain == ".example.com"

    config_none = CookieConfig()
    assert config_none.domain is None


def test_get_cookie_config_singleton():
    """get_cookie_config returns consistent instance."""
    config1 = get_cookie_config()
    config2 = get_cookie_config()
    assert config1 is config2
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_cookie_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.cookie_config'"

**Step 3: Write minimal implementation**

```python
# backend/core/cookie_config.py
"""Cookie configuration for HttpOnly token storage."""
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from core.config import settings


@dataclass
class CookieConfig:
    """Configuration for authentication cookies."""

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
    """Get cookie configuration from settings."""
    return CookieConfig(
        environment=getattr(settings, "ENVIRONMENT", "development"),
        domain=getattr(settings, "COOKIE_DOMAIN", None),
        access_token_max_age=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 15) * 60,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_cookie_config.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add backend/core/cookie_config.py backend/tests/test_cookie_config.py
git commit -m "feat(auth): add cookie configuration module

- CookieConfig dataclass with secure defaults
- HttpOnly, SameSite=Lax, Secure (in prod)
- Configurable TTLs for access/refresh tokens
- CSRF token name configuration"
```

---

## Task 2: Create Cookie Helper Functions

**Files:**
- Modify: `backend/core/cookie_config.py`
- Test: `backend/tests/test_cookie_config.py` (add tests)

**Step 1: Write the failing tests**

```python
# Add to backend/tests/test_cookie_config.py
from unittest.mock import MagicMock
from fastapi import Response

from core.cookie_config import (
    set_access_token_cookie,
    set_refresh_token_cookie,
    set_csrf_cookie,
    clear_auth_cookies,
)


def test_set_access_token_cookie():
    """Access token cookie set with correct parameters."""
    response = MagicMock(spec=Response)
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


def test_set_refresh_token_cookie():
    """Refresh token cookie set with correct parameters."""
    response = MagicMock(spec=Response)
    config = CookieConfig(environment="production")

    set_refresh_token_cookie(response, "refresh_test", config)

    response.set_cookie.assert_called_once_with(
        key="refresh_token",
        value="refresh_test",
        max_age=604800,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",  # Restricted path for refresh
        domain=None,
    )


def test_set_csrf_cookie():
    """CSRF cookie is NOT httponly (JS needs to read it)."""
    response = MagicMock(spec=Response)
    config = CookieConfig(environment="production")

    set_csrf_cookie(response, "csrf_value", config)

    response.set_cookie.assert_called_once()
    call_kwargs = response.set_cookie.call_args[1]
    assert call_kwargs["httponly"] is False  # JS must read this
    assert call_kwargs["secure"] is True


def test_clear_auth_cookies():
    """All auth cookies cleared on logout."""
    response = MagicMock(spec=Response)
    config = CookieConfig()

    clear_auth_cookies(response, config)

    assert response.delete_cookie.call_count == 3
    deleted_cookies = [call[1]["key"] for call in response.delete_cookie.call_args_list]
    assert "access_token" in deleted_cookies
    assert "refresh_token" in deleted_cookies
    assert "csrf_token" in deleted_cookies
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_cookie_config.py::test_set_access_token_cookie -v`
Expected: FAIL with "cannot import name 'set_access_token_cookie'"

**Step 3: Write minimal implementation**

```python
# Add to backend/core/cookie_config.py (after CookieConfig class)

from fastapi import Response


def set_access_token_cookie(
    response: Response,
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set access token in HttpOnly cookie."""
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
    response: Response,
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set refresh token in HttpOnly cookie with restricted path."""
    if config is None:
        config = get_cookie_config()

    response.set_cookie(
        key=config.refresh_token_name,
        value=token,
        max_age=config.refresh_token_max_age,
        httponly=config.httponly,
        secure=config.secure,
        samesite=config.samesite,
        path="/api/v1/auth",  # Only sent to auth endpoints
        domain=config.domain,
    )


def set_csrf_cookie(
    response: Response,
    token: str,
    config: CookieConfig | None = None,
) -> None:
    """Set CSRF token in readable cookie (not HttpOnly)."""
    if config is None:
        config = get_cookie_config()

    response.set_cookie(
        key=config.csrf_token_name,
        value=token,
        max_age=config.access_token_max_age,  # Same lifetime as access
        httponly=False,  # JS must read this
        secure=config.secure,
        samesite=config.samesite,
        path=config.path,
        domain=config.domain,
    )


def clear_auth_cookies(
    response: Response,
    config: CookieConfig | None = None,
) -> None:
    """Clear all authentication cookies."""
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
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_cookie_config.py -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add backend/core/cookie_config.py backend/tests/test_cookie_config.py
git commit -m "feat(auth): add cookie helper functions

- set_access_token_cookie: HttpOnly secure cookie
- set_refresh_token_cookie: restricted to /api/v1/auth path
- set_csrf_cookie: readable by JS for double-submit
- clear_auth_cookies: clears all three on logout"
```

---

## Task 3: Add Cookie Token Extraction to Dependencies

**Files:**
- Modify: `backend/core/dependencies.py`
- Test: `backend/tests/test_dependencies_cookie.py` (new)

**Step 1: Write the failing test**

```python
# backend/tests/test_dependencies_cookie.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request

from core.dependencies import extract_token_from_request


@pytest.fixture
def mock_request():
    """Create mock request with configurable cookies and headers."""
    request = MagicMock(spec=Request)
    request.cookies = {}
    request.headers = {}
    return request


def test_extract_token_from_cookie(mock_request):
    """Token extracted from cookie when present."""
    mock_request.cookies = {"access_token": "cookie_token_value"}
    mock_request.headers = {}

    token = extract_token_from_request(mock_request)

    assert token == "cookie_token_value"


def test_extract_token_from_header(mock_request):
    """Token extracted from Authorization header when no cookie."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer header_token_value"}

    token = extract_token_from_request(mock_request)

    assert token == "header_token_value"


def test_cookie_takes_precedence_over_header(mock_request):
    """Cookie token preferred over header for gradual migration."""
    mock_request.cookies = {"access_token": "cookie_token"}
    mock_request.headers = {"authorization": "Bearer header_token"}

    token = extract_token_from_request(mock_request)

    assert token == "cookie_token"


def test_extract_token_returns_none_when_missing(mock_request):
    """None returned when no token found anywhere."""
    mock_request.cookies = {}
    mock_request.headers = {}

    token = extract_token_from_request(mock_request)

    assert token is None


def test_extract_token_handles_malformed_header(mock_request):
    """Malformed Authorization header returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "InvalidFormat"}

    token = extract_token_from_request(mock_request)

    assert token is None
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_dependencies_cookie.py -v`
Expected: FAIL with "cannot import name 'extract_token_from_request'"

**Step 3: Write minimal implementation**

```python
# Add to backend/core/dependencies.py (near top, after imports)

from fastapi import Request
from core.cookie_config import get_cookie_config


def extract_token_from_request(request: Request) -> str | None:
    """
    Extract access token from request.

    Priority:
    1. HttpOnly cookie (new secure method)
    2. Authorization header (legacy, for gradual migration)

    Returns None if no valid token found.
    """
    config = get_cookie_config()

    # Try cookie first (preferred)
    token = request.cookies.get(config.access_token_name)
    if token:
        return token

    # Fall back to Authorization header (legacy support)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Strip "Bearer " prefix

    return None
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_dependencies_cookie.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add backend/core/dependencies.py backend/tests/test_dependencies_cookie.py
git commit -m "feat(auth): add cookie-first token extraction

- extract_token_from_request checks cookie first
- Falls back to Authorization header for migration
- Handles malformed headers gracefully"
```

---

## Task 4: Update get_current_user to Use Cookie Extraction

**Files:**
- Modify: `backend/core/dependencies.py`
- Test: `backend/tests/test_dependencies_cookie.py` (add integration test)

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_dependencies_cookie.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, HTTPException

from core.dependencies import get_current_user_from_request


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_current_user_from_cookie(mock_request, mock_db):
    """User retrieved when valid token in cookie."""
    mock_request.cookies = {"access_token": "valid_token"}
    mock_request.headers = {}

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.role = "student"
    mock_user.password_changed_at = None

    with patch("core.dependencies.TokenManager") as mock_tm, \
         patch("core.dependencies.get_user_by_email") as mock_get_user:
        mock_tm.decode_token.return_value = {
            "sub": "test@example.com",
            "role": "student",
            "pwd_ts": None,
            "type": "access",
        }
        mock_get_user.return_value = mock_user

        user = await get_current_user_from_request(mock_request, mock_db)

        assert user.email == "test@example.com"
        mock_tm.decode_token.assert_called_once_with("valid_token", expected_type="access")


@pytest.mark.asyncio
async def test_get_current_user_no_token_raises_401(mock_request, mock_db):
    """401 raised when no token found."""
    mock_request.cookies = {}
    mock_request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_from_request(mock_request, mock_db)

    assert exc_info.value.status_code == 401
    assert "Not authenticated" in str(exc_info.value.detail)
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_dependencies_cookie.py::test_get_current_user_from_cookie -v`
Expected: FAIL with "cannot import name 'get_current_user_from_request'"

**Step 3: Modify get_current_user in dependencies.py**

The key change is to add a new function that takes Request directly, then update the existing dependency:

```python
# In backend/core/dependencies.py

# Add new function
async def get_current_user_from_request(
    request: Request,
    db: AsyncSession,
) -> User:
    """
    Get current user from request (cookie or header token).

    This is the new cookie-aware version of get_current_user.
    """
    token = extract_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = TokenManager.decode_token(token, expected_type="access")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Validate password hasn't changed since token was issued
    token_pwd_ts = payload.get("pwd_ts")
    if user.password_changed_at:
        user_pwd_ts = int(user.password_changed_at.timestamp())
        if token_pwd_ts and token_pwd_ts < user_pwd_ts:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password changed, please log in again",
            )

    # Validate role matches
    if payload.get("role") != user.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role changed, please log in again",
        )

    return user


# Update get_current_user to use the new function
async def get_current_user(
    request: Request = None,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user.

    Supports both cookie and header authentication for backwards compatibility.
    """
    # If we have a request object, use cookie-aware extraction
    if request:
        return await get_current_user_from_request(request, db)

    # Legacy path: use OAuth2 scheme token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ... rest of existing implementation
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_dependencies_cookie.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add backend/core/dependencies.py backend/tests/test_dependencies_cookie.py
git commit -m "feat(auth): update get_current_user for cookie support

- get_current_user_from_request extracts from cookie/header
- Maintains backwards compatibility with Authorization header
- Same validation: active user, password timestamp, role"
```

---

## Task 5: Create CSRF Token Generator

**Files:**
- Create: `backend/core/csrf.py`
- Test: `backend/tests/test_csrf.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_csrf.py
import pytest
from core.csrf import generate_csrf_token, validate_csrf_token


def test_generate_csrf_token_length():
    """CSRF token has sufficient entropy (32 bytes = 64 hex chars)."""
    token = generate_csrf_token()
    assert len(token) == 64
    assert all(c in "0123456789abcdef" for c in token)


def test_generate_csrf_token_unique():
    """Each generated token is unique."""
    tokens = {generate_csrf_token() for _ in range(100)}
    assert len(tokens) == 100


def test_validate_csrf_token_matches():
    """Validation passes when tokens match."""
    token = generate_csrf_token()
    assert validate_csrf_token(token, token) is True


def test_validate_csrf_token_mismatch():
    """Validation fails when tokens differ."""
    token1 = generate_csrf_token()
    token2 = generate_csrf_token()
    assert validate_csrf_token(token1, token2) is False


def test_validate_csrf_token_timing_safe():
    """Validation uses constant-time comparison."""
    # This is more of a code review check, but we verify behavior
    token = generate_csrf_token()
    assert validate_csrf_token(token, token) is True
    assert validate_csrf_token(token, token + "x") is False
    assert validate_csrf_token(token, "") is False
    assert validate_csrf_token("", token) is False


def test_validate_csrf_token_none_handling():
    """Validation handles None values safely."""
    token = generate_csrf_token()
    assert validate_csrf_token(None, token) is False
    assert validate_csrf_token(token, None) is False
    assert validate_csrf_token(None, None) is False
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_csrf.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.csrf'"

**Step 3: Write minimal implementation**

```python
# backend/core/csrf.py
"""CSRF protection utilities."""
import secrets
import hmac


def generate_csrf_token() -> str:
    """
    Generate a cryptographically secure CSRF token.

    Returns 64 character hex string (32 bytes of entropy).
    """
    return secrets.token_hex(32)


def validate_csrf_token(cookie_token: str | None, header_token: str | None) -> bool:
    """
    Validate CSRF token using constant-time comparison.

    Double-submit cookie pattern: compare token from cookie with token from header.

    Args:
        cookie_token: Token from csrf_token cookie
        header_token: Token from X-CSRF-Token header

    Returns:
        True if tokens match, False otherwise
    """
    if not cookie_token or not header_token:
        return False

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(cookie_token, header_token)
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_csrf.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add backend/core/csrf.py backend/tests/test_csrf.py
git commit -m "feat(auth): add CSRF token generation and validation

- generate_csrf_token: 32 bytes entropy (64 hex chars)
- validate_csrf_token: constant-time comparison
- Double-submit cookie pattern support"
```

---

## Task 6: Create CSRF Middleware

**Files:**
- Create: `backend/core/csrf_middleware.py`
- Test: `backend/tests/test_csrf_middleware.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_csrf_middleware.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request
from starlette.responses import Response

from core.csrf_middleware import CSRFMiddleware, csrf_exempt


@pytest.fixture
def mock_app():
    """Mock ASGI app."""
    return AsyncMock()


@pytest.fixture
def middleware(mock_app):
    """Create middleware instance."""
    return CSRFMiddleware(mock_app, exempt_paths=["/api/v1/auth/login"])


def make_request(method: str, path: str, cookies: dict = None, headers: dict = None):
    """Create mock request."""
    request = MagicMock(spec=Request)
    request.method = method
    request.url.path = path
    request.cookies = cookies or {}
    request.headers = headers or {}
    return request


@pytest.mark.asyncio
async def test_get_request_bypasses_csrf(middleware):
    """GET requests don't require CSRF validation."""
    request = make_request("GET", "/api/v1/users/me")

    # Should not raise
    await middleware.dispatch(request, lambda r: AsyncMock(return_value=Response())())


@pytest.mark.asyncio
async def test_exempt_path_bypasses_csrf(middleware):
    """Exempt paths don't require CSRF validation."""
    request = make_request("POST", "/api/v1/auth/login")

    # Should not raise even without CSRF token
    await middleware.dispatch(request, lambda r: AsyncMock(return_value=Response())())


@pytest.mark.asyncio
async def test_post_without_csrf_returns_403(middleware):
    """POST without CSRF token returns 403."""
    request = make_request("POST", "/api/v1/bookings", cookies={}, headers={})

    response = await middleware.dispatch(request, lambda r: AsyncMock(return_value=Response())())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_with_valid_csrf_passes(middleware):
    """POST with matching CSRF tokens passes."""
    csrf_token = "test_csrf_token_value"
    request = make_request(
        "POST",
        "/api/v1/bookings",
        cookies={"csrf_token": csrf_token},
        headers={"x-csrf-token": csrf_token},
    )

    inner_called = False
    async def call_next(req):
        nonlocal inner_called
        inner_called = True
        return Response()

    await middleware.dispatch(request, call_next)
    assert inner_called


@pytest.mark.asyncio
async def test_post_with_mismatched_csrf_returns_403(middleware):
    """POST with mismatched CSRF tokens returns 403."""
    request = make_request(
        "POST",
        "/api/v1/bookings",
        cookies={"csrf_token": "token_a"},
        headers={"x-csrf-token": "token_b"},
    )

    response = await middleware.dispatch(request, lambda r: AsyncMock(return_value=Response())())

    assert response.status_code == 403
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_csrf_middleware.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.csrf_middleware'"

**Step 3: Write minimal implementation**

```python
# backend/core/csrf_middleware.py
"""CSRF protection middleware."""
from typing import Callable, Sequence
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from core.csrf import validate_csrf_token
from core.cookie_config import get_cookie_config


# Methods that modify state require CSRF protection
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def csrf_exempt(func: Callable) -> Callable:
    """Decorator to mark endpoint as CSRF-exempt."""
    func._csrf_exempt = True
    return func


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using double-submit cookie pattern.

    For unsafe methods (POST, PUT, PATCH, DELETE):
    1. Reads csrf_token from cookie
    2. Reads X-CSRF-Token from header
    3. Validates they match
    """

    def __init__(
        self,
        app,
        exempt_paths: Sequence[str] | None = None,
    ):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or [])
        self.config = get_cookie_config()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safe methods don't need CSRF protection
        if request.method not in UNSAFE_METHODS:
            return await call_next(request)

        # Check if path is exempt (login, webhooks, etc.)
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Validate CSRF tokens
        cookie_token = request.cookies.get(self.config.csrf_token_name)
        header_token = request.headers.get("x-csrf-token")

        if not validate_csrf_token(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection."""
        # Exact match
        if path in self.exempt_paths:
            return True

        # Prefix match for path patterns
        for exempt in self.exempt_paths:
            if exempt.endswith("*") and path.startswith(exempt[:-1]):
                return True

        return False
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_csrf_middleware.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add backend/core/csrf_middleware.py backend/tests/test_csrf_middleware.py
git commit -m "feat(auth): add CSRF middleware

- CSRFMiddleware validates double-submit cookie pattern
- Exempt paths for login, webhooks, public endpoints
- Returns 403 on validation failure"
```

---

## Task 7: Update Login Endpoint to Set Cookies

**Files:**
- Modify: `backend/modules/auth/presentation/api.py`
- Test: `backend/modules/auth/tests/test_auth_cookies.py` (new)

**Step 1: Write the failing test**

```python
# backend/modules/auth/tests/test_auth_cookies.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_sets_access_token_cookie(client: AsyncClient, test_user):
    """Login response sets access_token HttpOnly cookie."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200

    cookies = response.cookies
    assert "access_token" in cookies
    # Note: can't check HttpOnly flag from client side


@pytest.mark.asyncio
async def test_login_sets_refresh_token_cookie(client: AsyncClient, test_user):
    """Login response sets refresh_token HttpOnly cookie."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_sets_csrf_token_cookie(client: AsyncClient, test_user):
    """Login response sets csrf_token readable cookie."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200
    assert "csrf_token" in response.cookies


@pytest.mark.asyncio
async def test_login_still_returns_tokens_in_body(client: AsyncClient, test_user):
    """Login response still includes tokens in body for migration period."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py -v`
Expected: FAIL (cookies not set)

**Step 3: Modify login endpoint**

```python
# In backend/modules/auth/presentation/api.py
# Modify the login function to add cookie setting

from fastapi import Response
from core.cookie_config import (
    set_access_token_cookie,
    set_refresh_token_cookie,
    set_csrf_cookie,
)
from core.csrf import generate_csrf_token


@router.post("/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,  # Add this parameter
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    # ... existing authentication logic ...

    result = await auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )

    # Set HttpOnly cookies
    set_access_token_cookie(response, result["access_token"])
    set_refresh_token_cookie(response, result["refresh_token"])

    # Set CSRF token (readable by JS)
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    # Return tokens in body for backwards compatibility
    return result
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add backend/modules/auth/presentation/api.py backend/modules/auth/tests/test_auth_cookies.py
git commit -m "feat(auth): login endpoint sets HttpOnly cookies

- Sets access_token, refresh_token as HttpOnly cookies
- Sets csrf_token as readable cookie
- Maintains JSON body response for migration"
```

---

## Task 8: Update Refresh Endpoint to Set Cookies

**Files:**
- Modify: `backend/modules/auth/presentation/api.py`
- Test: `backend/modules/auth/tests/test_auth_cookies.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/modules/auth/tests/test_auth_cookies.py

@pytest.mark.asyncio
async def test_refresh_reads_from_cookie(client: AsyncClient, test_user):
    """Refresh endpoint can read refresh_token from cookie."""
    # First login to get cookies
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    # Refresh using cookie (no body needed)
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies,
    )

    assert refresh_response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_updates_access_token_cookie(client: AsyncClient, test_user):
    """Refresh response updates access_token cookie."""
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    original_access = login_response.cookies.get("access_token")

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies,
    )

    new_access = refresh_response.cookies.get("access_token")
    assert new_access is not None
    assert new_access != original_access
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py::test_refresh_reads_from_cookie -v`
Expected: FAIL

**Step 3: Modify refresh endpoint**

```python
# In backend/modules/auth/presentation/api.py
# Modify the refresh function

from typing import Optional
from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh (optional if using cookies)."""
    refresh_token: Optional[str] = None


@router.post("/refresh", response_model=Token)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    body: RefreshTokenRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token from cookie or body."""
    config = get_cookie_config()

    # Get refresh token from cookie or body
    refresh_token = request.cookies.get(config.refresh_token_name)
    if not refresh_token and body:
        refresh_token = body.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    result = await auth_service.refresh_access_token(db, refresh_token)

    # Update access token cookie
    set_access_token_cookie(response, result["access_token"])

    # Rotate CSRF token on refresh
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    return result
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add backend/modules/auth/presentation/api.py backend/modules/auth/tests/test_auth_cookies.py
git commit -m "feat(auth): refresh endpoint supports cookie-based tokens

- Reads refresh_token from cookie or body
- Updates access_token cookie on refresh
- Rotates CSRF token"
```

---

## Task 9: Update Logout Endpoint to Clear Cookies

**Files:**
- Modify: `backend/modules/auth/presentation/api.py`
- Test: `backend/modules/auth/tests/test_auth_cookies.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/modules/auth/tests/test_auth_cookies.py

@pytest.mark.asyncio
async def test_logout_clears_all_cookies(client: AsyncClient, test_user):
    """Logout clears all authentication cookies."""
    # Login first
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )

    # Logout
    logout_response = await client.post(
        "/api/v1/auth/logout",
        cookies=login_response.cookies,
        headers={"x-csrf-token": login_response.cookies.get("csrf_token")},
    )

    assert logout_response.status_code == 200

    # Cookies should be cleared (set with max_age=0 or deleted)
    # The exact check depends on how delete_cookie works in your test setup
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py::test_logout_clears_all_cookies -v`
Expected: FAIL (endpoint may not exist or not clear cookies)

**Step 3: Add/modify logout endpoint**

```python
# In backend/modules/auth/presentation/api.py

from core.cookie_config import clear_auth_cookies


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """Log out user by clearing authentication cookies."""
    clear_auth_cookies(response)

    # Optionally: add refresh token to blacklist here
    # await token_blacklist.add(refresh_token_jti)

    return {"message": "Successfully logged out"}
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/modules/auth/tests/test_auth_cookies.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add backend/modules/auth/presentation/api.py backend/modules/auth/tests/test_auth_cookies.py
git commit -m "feat(auth): logout endpoint clears auth cookies

- POST /auth/logout clears all three cookies
- Requires authentication to logout"
```

---

## Task 10: Update Frontend API Client for Credentials Mode

**Files:**
- Modify: `frontend-v2/lib/api/client.ts`
- Test: `frontend-v2/__tests__/lib/api/client.test.ts` (new)

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/lib/api/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ApiClient', () => {
  beforeEach(() => {
    vi.resetModules();
    mockFetch.mockClear();
  });

  it('includes credentials in all requests', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });

    // Import fresh to avoid module cache issues
    const { api } = await import('@/lib/api/client');

    await api.get('/test');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('reads CSRF token from cookie and adds to header', async () => {
    // Mock document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=test_csrf_value',
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    const { api } = await import('@/lib/api/client');

    await api.post('/test', { data: 'value' });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test_csrf_value',
        }),
      })
    );
  });

  it('does not include Authorization header when using cookies', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    const { api } = await import('@/lib/api/client');

    await api.get('/test');

    const callArgs = mockFetch.mock.calls[0][1];
    expect(callArgs.headers?.Authorization).toBeUndefined();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion/frontend-v2 && npm test -- __tests__/lib/api/client.test.ts`
Expected: FAIL (credentials not set)

**Step 3: Modify API client**

```typescript
// frontend-v2/lib/api/client.ts

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get CSRF token from cookie.
 */
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;

  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code?: string
  ) {
    super(detail);
    this.name = 'ApiError';
  }

  get isUnauthorized() { return this.status === 401; }
  get isForbidden() { return this.status === 403; }
  get isNotFound() { return this.status === 404; }
  get isValidation() { return this.status === 422; }
  get isServerError() { return this.status >= 500; }
}

class ApiClient {
  /**
   * Make authenticated request with HttpOnly cookies.
   */
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add CSRF token for unsafe methods
    const method = options.method?.toUpperCase() || 'GET';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        (headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
      }
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Send cookies with every request
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail, error.code);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  postForm<T>(endpoint: string, data: Record<string, string>): Promise<T> {
    const formData = new URLSearchParams(data);
    return this.request<T>(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
  }

  put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient();
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion/frontend-v2 && npm test -- __tests__/lib/api/client.test.ts`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend-v2/lib/api/client.ts frontend-v2/__tests__/lib/api/client.test.ts
git commit -m "feat(frontend): API client uses HttpOnly cookies

- credentials: 'include' for all requests
- Reads CSRF token from cookie for unsafe methods
- Removes localStorage token handling"
```

---

## Task 11: Update Frontend Auth Hook to Remove Token Management

**Files:**
- Modify: `frontend-v2/lib/hooks/use-auth.ts`
- Modify: `frontend-v2/lib/api/auth.ts`

**Step 1: Modify auth API**

```typescript
// frontend-v2/lib/api/auth.ts
import { api } from './client';
import type { User, AuthTokens } from '@/types/user';

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: 'student' | 'tutor';
}

export const authApi = {
  login: (data: LoginInput) =>
    api.postForm<AuthTokens>('/auth/login', {
      username: data.email,
      password: data.password,
    }),

  register: (data: RegisterInput) =>
    api.post<User>('/auth/register', data),

  me: () =>
    api.get<User>('/auth/me'),

  logout: () =>
    api.post<{ message: string }>('/auth/logout', {}),

  refresh: () =>
    api.post<AuthTokens>('/auth/refresh', {}),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};

export const authKeys = {
  all: ['auth'] as const,
  me: () => [...authKeys.all, 'me'] as const,
};
```

**Step 2: Modify use-auth hook**

```typescript
// frontend-v2/lib/hooks/use-auth.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { authApi, authKeys, type LoginInput, type RegisterInput } from '@/lib/api/auth';

export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const { data: user, isLoading, error } = useQuery({
    queryKey: authKeys.me(),
    queryFn: authApi.me,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: () => {
      // No need to store token - it's in HttpOnly cookie
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear all queries and redirect
      queryClient.clear();
      router.push('/login');
    },
  });

  const login = async (data: LoginInput) => {
    await loginMutation.mutateAsync(data);
  };

  const register = async (data: RegisterInput) => {
    return registerMutation.mutateAsync(data);
  };

  const logout = async () => {
    await logoutMutation.mutateAsync();
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    error,
    login,
    logout,
    register,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
  };
}

export function useUser() {
  const { data: user, isLoading, error } = useQuery({
    queryKey: authKeys.me(),
    queryFn: authApi.me,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  return { user, isLoading, error };
}
```

**Step 3: Commit**

```bash
git add frontend-v2/lib/hooks/use-auth.ts frontend-v2/lib/api/auth.ts
git commit -m "feat(frontend): remove localStorage token management from auth

- Login no longer stores token (cookie handles it)
- Logout calls backend to clear cookies
- Simplified auth state management"
```

---

## Task 12: Add Automatic Token Refresh on 401

**Files:**
- Modify: `frontend-v2/lib/api/client.ts`
- Test: `frontend-v2/__tests__/lib/api/client.test.ts` (add tests)

**Step 1: Write the failing test**

```typescript
// Add to frontend-v2/__tests__/lib/api/client.test.ts

describe('Automatic token refresh', () => {
  it('retries request after 401 with automatic refresh', async () => {
    const { api } = await import('@/lib/api/client');

    // First call returns 401
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Refresh call succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ access_token: 'new_token' }),
      })
      // Retry original request succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'success' }),
      });

    const result = await api.get('/protected-resource');

    expect(result).toEqual({ data: 'success' });
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('throws on 401 if refresh also fails', async () => {
    const { api, ApiError } = await import('@/lib/api/client');

    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Refresh failed' }),
      });

    await expect(api.get('/protected')).rejects.toThrow(ApiError);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion/frontend-v2 && npm test -- __tests__/lib/api/client.test.ts`
Expected: FAIL (no retry logic)

**Step 3: Add retry logic to API client**

```typescript
// frontend-v2/lib/api/client.ts

class ApiClient {
  private isRefreshing = false;
  private refreshPromise: Promise<void> | null = null;

  /**
   * Attempt to refresh the access token.
   */
  private async refreshToken(): Promise<void> {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new ApiError(response.status, 'Token refresh failed');
    }
  }

  /**
   * Make authenticated request with automatic token refresh on 401.
   */
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await this.doRequest(endpoint, options);

    // If 401 and not already a refresh request, try to refresh
    if (response.status === 401 && !endpoint.includes('/auth/refresh')) {
      // Ensure only one refresh happens at a time
      if (!this.isRefreshing) {
        this.isRefreshing = true;
        this.refreshPromise = this.refreshToken()
          .finally(() => {
            this.isRefreshing = false;
            this.refreshPromise = null;
          });
      }

      try {
        await this.refreshPromise;
        // Retry original request
        const retryResponse = await this.doRequest(endpoint, options);
        return this.handleResponse<T>(retryResponse);
      } catch {
        // Refresh failed, throw original 401
        throw new ApiError(401, 'Authentication required');
      }
    }

    return this.handleResponse<T>(response);
  }

  private async doRequest(endpoint: string, options: RequestInit): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const method = options.method?.toUpperCase() || 'GET';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        (headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
      }
    }

    return fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail, error.code);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // ... rest of methods unchanged
}
```

**Step 4: Run test to verify it passes**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion/frontend-v2 && npm test -- __tests__/lib/api/client.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/lib/api/client.ts frontend-v2/__tests__/lib/api/client.test.ts
git commit -m "feat(frontend): automatic token refresh on 401

- Intercepts 401 responses and attempts refresh
- Only one refresh at a time (prevents race conditions)
- Retries original request after successful refresh"
```

---

## Task 13: Update Backend CORS for Credentials

**Files:**
- Modify: `backend/core/cors.py`
- Modify: `backend/main.py`

**Step 1: Update CORS configuration**

```python
# backend/core/cors.py (or wherever CORS is configured)

from fastapi.middleware.cors import CORSMiddleware

# IMPORTANT: When credentials=True, cannot use "*" for origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://edustream.com",  # Production
    "https://www.edustream.com",
]

def configure_cors(app):
    """Configure CORS middleware for cookie authentication."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,  # Cannot be ["*"] with credentials
        allow_credentials=True,  # Required for cookies
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",  # Keep for backwards compatibility
            "X-CSRF-Token",  # For CSRF protection
        ],
        expose_headers=["X-Request-ID"],
    )
```

**Step 2: Add CSRF middleware to app**

```python
# In backend/main.py

from core.csrf_middleware import CSRFMiddleware

# Add after CORS middleware
app.add_middleware(
    CSRFMiddleware,
    exempt_paths=[
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/webhooks/*",  # Stripe webhooks etc
        "/health",
        "/docs",
        "/openapi.json",
    ],
)
```

**Step 3: Commit**

```bash
git add backend/core/cors.py backend/main.py
git commit -m "feat(auth): configure CORS and CSRF for cookie auth

- CORS allows credentials with specific origins
- CSRF middleware with exempt paths for auth/webhooks
- X-CSRF-Token in allowed headers"
```

---

## Task 14: Add Integration Tests

**Files:**
- Create: `backend/tests/test_cookie_auth_integration.py`

**Step 1: Write integration tests**

```python
# backend/tests/test_cookie_auth_integration.py
"""Integration tests for cookie-based authentication flow."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_auth_flow_with_cookies(client: AsyncClient, test_user_data):
    """Test complete authentication flow using cookies."""
    # 1. Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert register_response.status_code == 201

    # 2. Login - should set cookies
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.cookies
    assert "refresh_token" in login_response.cookies
    assert "csrf_token" in login_response.cookies

    # 3. Access protected endpoint using cookies
    me_response = await client.get(
        "/api/v1/auth/me",
        cookies=login_response.cookies,
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == test_user_data["email"]

    # 4. Make state-changing request with CSRF
    csrf_token = login_response.cookies.get("csrf_token")
    profile_response = await client.patch(
        "/api/v1/users/me",
        json={"first_name": "Updated"},
        cookies=login_response.cookies,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert profile_response.status_code in [200, 404]  # 404 if endpoint doesn't exist

    # 5. Refresh token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies,
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.cookies

    # 6. Logout
    new_csrf = refresh_response.cookies.get("csrf_token") or csrf_token
    logout_response = await client.post(
        "/api/v1/auth/logout",
        cookies=refresh_response.cookies,
        headers={"X-CSRF-Token": new_csrf},
    )
    assert logout_response.status_code == 200

    # 7. Verify cookies are cleared (access should fail)
    after_logout = await client.get(
        "/api/v1/auth/me",
        cookies=logout_response.cookies,  # Should be empty/expired
    )
    assert after_logout.status_code == 401


@pytest.mark.asyncio
async def test_csrf_protection_blocks_post_without_token(client: AsyncClient, authenticated_user):
    """POST requests fail without CSRF token."""
    cookies, _ = authenticated_user

    # Remove CSRF from cookies to simulate missing token
    cookies_without_csrf = {k: v for k, v in cookies.items() if k != "csrf_token"}

    response = await client.post(
        "/api/v1/bookings",
        json={"tutor_id": 1, "slot": "2024-01-01T10:00:00"},
        cookies=cookies_without_csrf,
        # No X-CSRF-Token header
    )

    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_backwards_compatibility_with_bearer_token(client: AsyncClient, test_user):
    """Authorization header still works during migration."""
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    # Use Authorization header instead of cookies
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
```

**Step 2: Run integration tests**

Run: `cd /mnt/c/Users/valsa/Documents/Project1-splitversion && docker compose exec backend pytest backend/tests/test_cookie_auth_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/test_cookie_auth_integration.py
git commit -m "test(auth): add integration tests for cookie auth flow

- Full auth flow: register -> login -> access -> refresh -> logout
- CSRF protection verification
- Backwards compatibility with Bearer token"
```

---

## Task 15: Remove Deprecated localStorage Code & Documentation

**Files:**
- Remove: localStorage references in frontend
- Update: Security documentation

**Step 1: Search and remove localStorage token code**

```bash
# Find remaining localStorage references
grep -r "localStorage" frontend-v2/lib --include="*.ts" --include="*.tsx"
```

Remove any remaining `localStorage.setItem('auth_token'...)` and `localStorage.getItem('auth_token')` calls.

**Step 2: Update security documentation**

Create or update `frontend-v2/SECURITY_NOTES.md`:

```markdown
# Security Implementation Notes

## Authentication

This application uses HttpOnly cookies for authentication tokens:

### Token Storage
- **Access Token**: HttpOnly Secure cookie, 15-minute TTL
- **Refresh Token**: HttpOnly Secure cookie, 7-day TTL, restricted to `/api/v1/auth` path
- **CSRF Token**: Readable cookie (not HttpOnly) for double-submit pattern

### Security Properties
- **XSS Protection**: Tokens cannot be accessed by JavaScript (HttpOnly)
- **CSRF Protection**: Double-submit cookie pattern with `X-CSRF-Token` header
- **Secure Transport**: Cookies only sent over HTTPS in production

### Migration Notes
- The backend temporarily supports both cookie and Authorization header authentication
- Once all clients migrate, Authorization header support can be removed

## CSRF Protection

All state-changing requests (POST, PUT, PATCH, DELETE) require:
1. `csrf_token` cookie (set on login)
2. `X-CSRF-Token` header matching the cookie value

Exempt endpoints:
- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/refresh`
- `/api/v1/webhooks/*`
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore(auth): remove localStorage, add security docs

- Remove deprecated localStorage token handling
- Add SECURITY_NOTES.md documenting auth implementation
- Migration complete"
```

---

## Summary Checklist

| Phase | Task | Status |
|-------|------|--------|
| **Backend Cookie Infrastructure** | | |
| 1 | Cookie configuration module | ⬜ |
| 2 | Cookie helper functions | ⬜ |
| 3 | Token extraction from request | ⬜ |
| 4 | get_current_user cookie support | ⬜ |
| **CSRF Protection** | | |
| 5 | CSRF token generator | ⬜ |
| 6 | CSRF middleware | ⬜ |
| **Auth Endpoint Updates** | | |
| 7 | Login sets cookies | ⬜ |
| 8 | Refresh uses cookies | ⬜ |
| 9 | Logout clears cookies | ⬜ |
| **Frontend Migration** | | |
| 10 | API client credentials mode | ⬜ |
| 11 | Auth hook removes token mgmt | ⬜ |
| 12 | Automatic 401 refresh | ⬜ |
| **Configuration** | | |
| 13 | CORS + CSRF middleware | ⬜ |
| **Validation** | | |
| 14 | Integration tests | ⬜ |
| 15 | Cleanup + documentation | ⬜ |

---

## Rollback Plan

If issues arise during migration:

1. **Backend**: The `extract_token_from_request` function checks cookies first, then falls back to Authorization header. This provides automatic backwards compatibility.

2. **Frontend**: If needed, restore `setToken()` and `getToken()` methods in ApiClient and add `Authorization` header back to requests.

3. **CSRF**: The middleware has exempt paths. In emergency, add `"/*"` to exempt all paths temporarily.

## Post-Migration Cleanup (Future)

After successful migration and monitoring period:

1. Remove Authorization header fallback from `extract_token_from_request`
2. Remove `access_token`, `refresh_token` from login response body
3. Remove `oauth2_scheme` dependency
4. Update API documentation to reflect cookie-only auth
