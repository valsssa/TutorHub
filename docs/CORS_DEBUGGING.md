# CORS Debugging Playbook

This document explains how CORS works in EduStream and how to debug CORS-related issues.

## Quick Reference

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `https://edustream.valsa.solutions,http://localhost:3000` |
| `ENVIRONMENT` | Runtime environment (affects CORS caching) | `production`, `development` |

### Common CORS Origins by Environment

**Production:**
```bash
CORS_ORIGINS=https://edustream.valsa.solutions,https://api.valsa.solutions
```

**Development:**
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000
```

## Understanding CORS Errors

### Key Insight: CORS Errors Often Hide Real Errors

When a browser shows a CORS error, the actual problem is often:

1. **500 Internal Server Error** - Backend crashed, no CORS headers in error response
2. **429 Too Many Requests** - Rate limited, no CORS headers in 429 response
3. **401/403 Authentication Error** - But without CORS headers
4. **502/503/504 Gateway Errors** - Reverse proxy issue

**How to diagnose:**
```bash
# Check what the server actually returns
curl -v -X GET "https://api.valsa.solutions/api/v1/notifications" \
  -H "Origin: https://edustream.valsa.solutions" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test preflight
curl -v -X OPTIONS "https://api.valsa.solutions/api/v1/notifications" \
  -H "Origin: https://edustream.valsa.solutions" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization"
```

### CORS Test Endpoint

Use the built-in CORS test endpoint to verify configuration:

```bash
# Test from allowed origin
curl -v "https://api.valsa.solutions/api/v1/cors-test" \
  -H "Origin: https://edustream.valsa.solutions"

# Test from disallowed origin
curl -v "https://api.valsa.solutions/api/v1/cors-test" \
  -H "Origin: https://evil.com"
```

Expected response:
```json
{
  "cors_debug": {
    "request": {
      "origin": "https://edustream.valsa.solutions",
      "method": "GET"
    },
    "configuration": {
      "allowed_origins": ["https://edustream.valsa.solutions", ...],
      "origin_allowed": true,
      "environment": "production"
    },
    "response_headers": {
      "Access-Control-Allow-Origin": "https://edustream.valsa.solutions",
      "Access-Control-Allow-Credentials": "true",
      ...
    }
  }
}
```

## Common Issues and Solutions

### Issue 1: "No 'Access-Control-Allow-Origin' header present"

**Symptoms:**
- Browser console shows CORS error
- Network tab shows the request with status 0 or hidden status

**Root Causes:**

1. **Origin not in allowed list**
   ```bash
   # Check current CORS_ORIGINS
   docker compose exec backend env | grep CORS

   # Add missing origin to .env
   CORS_ORIGINS=https://edustream.valsa.solutions,https://your-new-origin.com
   ```

2. **Server error (500) with no CORS headers**
   ```bash
   # Check backend logs for the actual error
   docker compose logs backend --tail=100

   # The fix: Our CORSErrorMiddleware now adds headers to error responses
   ```

3. **Rate limiting (429) without CORS headers**
   ```bash
   # Wait and retry, or check rate limit configuration
   # The fix: Our custom rate limit handler now includes CORS headers
   ```

### Issue 2: Preflight Request Fails

**Symptoms:**
- OPTIONS request returns 403, 405, or 429
- GET/POST works in curl but not in browser

**Root Causes:**

1. **Rate limiting blocks OPTIONS**
   ```bash
   # OPTIONS should not be rate limited
   # Our implementation exempts OPTIONS from rate limiting
   ```

2. **Authentication middleware blocks OPTIONS**
   ```bash
   # OPTIONS should not require authentication
   # Verify the endpoint doesn't have auth on OPTIONS method
   ```

### Issue 3: Credentials Not Sent

**Symptoms:**
- Request works without auth but fails with auth
- Cookies not included in cross-origin requests

**Root Cause:**
- `Access-Control-Allow-Credentials: true` must be set
- Origin must be specific (not `*`) when using credentials

**Solution:**
Our configuration always sets `allow_credentials=True` with specific origins.

### Issue 4: WebSocket CORS Error

**Symptoms:**
- WebSocket connection fails with 4003 code
- Works in local dev but not in production

**Root Causes:**

1. **Origin not in WebSocket allowed list**
   ```python
   # Check backend/modules/messages/websocket.py
   # WebSocket origins are separate from HTTP CORS
   ```

2. **Missing wss:// protocol in production**
   ```bash
   # Ensure WebSocket URL uses wss:// in production
   # Check frontend/shared/utils/url.ts for URL construction
   ```

## Testing Checklist

### Local Development
```bash
# 1. Start services
docker compose up -d

# 2. Test health endpoint (no CORS needed)
curl http://localhost:8000/health

# 3. Test CORS endpoint
curl -v http://localhost:8000/api/v1/cors-test \
  -H "Origin: http://localhost:3000"

# 4. Test authenticated endpoint
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"student123"}' | jq -r '.access_token')

curl -v http://localhost:8000/api/v1/notifications \
  -H "Origin: http://localhost:3000" \
  -H "Authorization: Bearer $TOKEN"

# 5. Test WebSocket
# Open browser console on http://localhost:3000 and run:
# new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_TOKEN')
```

### Production (Cloudflare)
```bash
# 1. Test CORS endpoint
curl -v https://api.valsa.solutions/api/v1/cors-test \
  -H "Origin: https://edustream.valsa.solutions"

# 2. Verify headers in response
# Should include:
# - Access-Control-Allow-Origin: https://edustream.valsa.solutions
# - Access-Control-Allow-Credentials: true

# 3. Test preflight
curl -v -X OPTIONS https://api.valsa.solutions/api/v1/notifications \
  -H "Origin: https://edustream.valsa.solutions" \
  -H "Access-Control-Request-Method: GET"

# Should return 204 with CORS headers
```

## Architecture

### Middleware Stack (Order of Execution)

```
Request →
  1. CORSErrorMiddleware (catches missing CORS headers)
  2. CORSMiddleware (adds CORS headers to successful responses)
  3. TracingMiddleware
  4. SecurityHeadersMiddleware
  5. ResponseCacheMiddleware
  6. GZipMiddleware
  7. SlowAPIMiddleware (rate limiting)
  → Route Handler
  → Response
```

### Exception Handlers

- `RateLimitExceeded` → `create_cors_rate_limit_handler()` (includes CORS headers)
- `HTTPException` → `create_cors_http_exception_handler()` (includes CORS headers)
- Unhandled exceptions → `CORSErrorMiddleware` catches and adds CORS headers

### Files

| File | Purpose |
|------|---------|
| `backend/core/cors.py` | CORS utilities and middleware |
| `backend/main.py` | CORS configuration and middleware registration |
| `backend/core/config.py` | Default CORS origins |
| `backend/modules/messages/websocket.py` | WebSocket origin validation |

**Note:** Production uses Cloudflare for SSL termination and edge caching. CORS is handled at the application level.

## Decisions Log

| Decision | Why | Where |
|----------|-----|-------|
| Use specific origins, not `*` | Required for credentials, better security | `main.py`, `config.py` |
| Custom rate limit handler | Default handler lacks CORS headers | `cors.py`, `main.py` |
| CORSErrorMiddleware | Catch errors that bypass CORSMiddleware | `cors.py` |
| Lowercase origin comparison | Case-insensitive origin matching | `cors.py` |
| Include localhost:8000 in dev | Swagger UI needs CORS | `config.py` |

## Troubleshooting Commands

```bash
# Check what origins are configured
docker compose exec backend python -c "from core.cors import get_cors_origins; print(get_cors_origins())"

# Check environment
docker compose exec backend env | grep -E "CORS|ENVIRONMENT"

# Watch backend logs for errors
docker compose logs -f backend | grep -E "ERROR|CORS|origin"

# Test from browser console
fetch('https://api.valsa.solutions/api/v1/cors-test', {
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```
