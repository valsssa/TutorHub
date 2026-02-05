# CORS Single Source of Truth Refactoring

**Date:** 2026-02-05
**Status:** Ready for Implementation
**Goal:** World-class CORS implementation with single source of truth

## Executive Summary

Consolidate CORS configuration from 3 files (~400 lines) into 1 file (~120 lines) while maintaining all necessary functionality. The extra middleware layers are required due to Starlette limitations, but the code can be dramatically simplified.

## Current State Analysis

### Problems

| Issue | Impact |
|-------|--------|
| Origins parsed in 3 places | Inconsistency risk, maintenance burden |
| 309 lines in cors.py | Overcomplicated, hard to understand |
| Debug endpoints in production | Unnecessary attack surface |
| Defaults hardcoded in multiple files | Single source of truth violation |

### What's Actually Needed (Confirmed by Research)

| Component | Needed? | Reason |
|-----------|---------|--------|
| `CORSMiddleware` | ✅ Yes | Standard CORS handling |
| `CORSErrorMiddleware` | ✅ Yes | Starlette doesn't add CORS to 500 errors |
| Rate limit handler | ✅ Yes | slowapi exceptions bypass all middleware |
| HTTP exception handler | ⚠️ Optional | CORSErrorMiddleware covers this |
| Debug endpoints | ❌ No | Remove from production |

## Target Architecture

### Single Source of Truth: `core/cors.py` (~120 lines)

```
┌─────────────────────────────────────────────────────────────┐
│                      core/cors.py                           │
├─────────────────────────────────────────────────────────────┤
│  CORSConfig (dataclass)                                     │
│  ├── origins: list[str]         # From CORS_ORIGINS env    │
│  ├── methods: list[str]         # GET, POST, PUT, etc.     │
│  ├── headers: list[str]         # Authorization, etc.      │
│  ├── expose_headers: list[str]  # X-RateLimit-*, etc.      │
│  ├── max_age: int               # 86400 prod, 600 dev      │
│  └── credentials: bool          # True (for cookies)       │
├─────────────────────────────────────────────────────────────┤
│  get_cors_config() -> CORSConfig                            │
│  ├── Reads CORS_ORIGINS from environment                    │
│  ├── Falls back to ENVIRONMENT-based defaults               │
│  └── Returns frozen config (immutable)                      │
├─────────────────────────────────────────────────────────────┤
│  CORSMiddleware (re-export from starlette)                  │
├─────────────────────────────────────────────────────────────┤
│  CORSSafetyNetMiddleware                                    │
│  ├── Ensures CORS headers on ALL responses                  │
│  ├── Catches 500 errors that bypass CORSMiddleware          │
│  └── ~40 lines (simplified from 70)                         │
├─────────────────────────────────────────────────────────────┤
│  cors_exception_handler()                                   │
│  ├── Universal handler for all exceptions                   │
│  ├── Includes CORS headers                                  │
│  └── Works for HTTPException, RateLimitExceeded, etc.       │
├─────────────────────────────────────────────────────────────┤
│  setup_cors(app: FastAPI) -> None                           │
│  ├── Single function to configure everything                │
│  ├── Adds middlewares in correct order                      │
│  └── Registers exception handlers                           │
└─────────────────────────────────────────────────────────────┘
```

### Usage in main.py (2 lines)

```python
from core.cors import setup_cors

# In app initialization
setup_cors(app)
```

## Implementation Plan

### Phase 1: Create New cors.py (~120 lines)

```python
"""
CORS Configuration - Single Source of Truth

All CORS settings are defined here. No other file should parse CORS_ORIGINS
or define CORS-related constants.
"""

import os
import logging
from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class CORSConfig:
    """Immutable CORS configuration."""
    origins: tuple[str, ...]
    methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
        "X-CSRF-Token",
    )
    expose_headers: tuple[str, ...] = (
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Content-Disposition",
    )
    max_age: int = 86400
    credentials: bool = True


def get_cors_config() -> CORSConfig:
    """
    Get CORS configuration from environment.

    Priority:
    1. CORS_ORIGINS environment variable (comma-separated)
    2. Environment-based defaults (production vs development)
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    raw_origins = os.getenv("CORS_ORIGINS", "")

    if raw_origins:
        origins = tuple(
            o.strip().rstrip("/").lower()
            for o in raw_origins.split(",")
            if o.strip().startswith(("http://", "https://"))
        )
    elif env == "production":
        origins = (
            "https://edustream.valsa.solutions",
            "https://api.valsa.solutions",
        )
    else:
        origins = (
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        )

    max_age = 86400 if env == "production" else 600

    return CORSConfig(origins=origins, max_age=max_age)


# Global config instance (loaded once at import)
_config: CORSConfig | None = None

def _get_config() -> CORSConfig:
    global _config
    if _config is None:
        _config = get_cors_config()
    return _config


# =============================================================================
# MIDDLEWARE
# =============================================================================

class CORSSafetyNetMiddleware(BaseHTTPMiddleware):
    """
    Safety net that ensures CORS headers on ALL responses.

    Why needed: Starlette's CORSMiddleware doesn't add headers to:
    - 500 errors from ServerErrorMiddleware
    - Responses from exception handlers
    - Any response that bypasses the middleware chain

    This middleware runs AFTER CORSMiddleware and adds missing headers.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.config = _get_config()

    async def dispatch(self, request: Request, call_next: Callable):
        origin = request.headers.get("origin", "").lower().rstrip("/")

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception("Unhandled exception in request")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        # Add CORS headers if missing and origin is allowed
        if "access-control-allow-origin" not in response.headers:
            if origin in self.config.origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Vary"] = "Origin"

        return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

def create_cors_exception_handler():
    """
    Create exception handler that includes CORS headers.

    Works for HTTPException, RateLimitExceeded, and any other exception.
    """
    config = _get_config()

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        origin = request.headers.get("origin", "").lower().rstrip("/")

        # Determine status code and detail
        if isinstance(exc, HTTPException):
            status_code = exc.status_code
            detail = exc.detail
        elif hasattr(exc, "status_code"):
            status_code = exc.status_code
            detail = str(exc)
        else:
            status_code = 500
            detail = "Internal server error"

        headers = {}
        if origin in config.origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Vary"] = "Origin"

        # Add Retry-After for rate limits
        if hasattr(exc, "retry_after"):
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers=headers,
        )

    return handler


# =============================================================================
# SETUP FUNCTION
# =============================================================================

def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS for the application.

    Call this once during app initialization. This is the ONLY place
    where CORS middleware and handlers should be configured.
    """
    config = _get_config()

    logger.info(f"CORS origins: {config.origins}")
    logger.info(f"CORS max_age: {config.max_age}s")

    # Register exception handlers (run before middleware)
    from slowapi.errors import RateLimitExceeded
    handler = create_cors_exception_handler()
    app.add_exception_handler(RateLimitExceeded, handler)
    app.add_exception_handler(HTTPException, handler)
    app.add_exception_handler(Exception, handler)

    # Add Starlette's CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.origins),
        allow_credentials=config.credentials,
        allow_methods=list(config.methods),
        allow_headers=list(config.headers),
        expose_headers=list(config.expose_headers),
        max_age=config.max_age,
    )

    # Add safety net middleware (runs after CORSMiddleware)
    app.add_middleware(CORSSafetyNetMiddleware)
```

### Phase 2: Update main.py

Remove all CORS-related code (~80 lines) and replace with:

```python
from core.cors import setup_cors

# After app = FastAPI(...)
setup_cors(app)
```

### Phase 3: Update config.py

Remove `CORS_ORIGINS` field entirely. CORS configuration now lives only in `core/cors.py`.

### Phase 4: Remove Debug Endpoints

Remove from main.py:
- `GET /api/v1/cors-test`
- `OPTIONS /api/v1/cors-test`

These are security risks in production and unnecessary with proper logging.

### Phase 5: Update WebSocket Origin Validation

Update `backend/modules/messages/websocket.py` to use the shared config:

```python
from core.cors import _get_config

def is_valid_ws_origin(origin: str | None) -> bool:
    """Validate WebSocket connection origin."""
    if not origin:
        return True  # Allow non-browser clients

    config = _get_config()
    normalized = origin.lower().rstrip("/")
    return normalized in config.origins
```

### Phase 6: Update Tests

Update `backend/tests/test_cors.py` to test the new API:
- Test `get_cors_config()` with different environments
- Test `CORSSafetyNetMiddleware` adds missing headers
- Test `create_cors_exception_handler()` for various exceptions
- Test `setup_cors()` configures app correctly

## File Changes Summary

| File | Action | Lines Before | Lines After |
|------|--------|--------------|-------------|
| `core/cors.py` | Rewrite | 309 | ~120 |
| `main.py` | Simplify | ~80 CORS lines | 2 |
| `core/config.py` | Remove CORS_ORIGINS | 15 | 0 |
| `modules/messages/websocket.py` | Use shared config | 52 | 10 |
| `tests/test_cors.py` | Update for new API | 385 | ~200 |
| `/api/v1/cors-test` endpoints | Delete | 50 | 0 |

**Total: ~400 lines → ~120 lines (70% reduction)**

## Benefits

1. **Single Source of Truth**: All CORS config in one file
2. **Simpler API**: `setup_cors(app)` - one function call
3. **Immutable Config**: Frozen dataclass prevents accidental modification
4. **Better Logging**: Clear startup logs showing CORS configuration
5. **Easier Testing**: Config is injectable via `get_cors_config()`
6. **Secure by Default**: No debug endpoints in production
7. **Type Safe**: Full type hints, mypy compatible

## Security Considerations

- ✅ No wildcard origins
- ✅ Explicit credentials handling
- ✅ Origin validation before adding headers
- ✅ Vary: Origin header for cache safety
- ✅ No debug endpoints in production
- ✅ Rate limit exceptions include CORS headers

## Rollback Plan

If issues occur:
1. Revert to previous cors.py
2. Revert main.py CORS configuration
3. All changes are in version control
