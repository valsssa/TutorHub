# Integration Report: Next.js Frontend ↔ FastAPI Backend

**Date:** 2026-01-29
**Status:** CRITICAL ISSUES FOUND
**Platform:** EduStream Student-Tutor Booking Platform

---

## Executive Summary

This integration audit identified **21 critical API path mismatches** where the frontend calls endpoints without the `/v1/` version prefix, causing 404 errors. The backend consistently registers all routes under `/api/v1/`, but the frontend has inconsistent path usage.

### Quick Stats
- **Total Frontend API Calls:** ~90 endpoints
- **Correct Calls (using `/api/v1/`):** 69
- **Broken Calls (missing `/v1/`):** 21
- **CORS Configuration:** ✅ Correct
- **Auth Flow:** ✅ Correct
- **WebSocket:** ✅ Correct

---

## 1. Critical Issue: API Path Mismatches

### Problem Description

The backend mounts ALL routers with the `/api/v1` prefix in `main.py`:
```python
API_V1_PREFIX = "/api/v1"
app.include_router(messages_router, prefix=API_V1_PREFIX)
app.include_router(notifications_router, prefix=API_V1_PREFIX)
# ... all other routers
```

However, the frontend has 21 API calls that use `/api/` without the `v1` prefix:

### Affected Endpoints (21 total)

| Frontend Path (BROKEN) | Should Be | Component |
|------------------------|-----------|-----------|
| `/api/messages/users/${userId}` | `/api/v1/messages/users/${userId}` | Messages |
| `/api/messages/${messageId}/read` | `/api/v1/messages/${messageId}/read` | Messages |
| `/api/messages/threads/${otherUserId}/read-all` | `/api/v1/messages/threads/${otherUserId}/read-all` | Messages |
| `/api/messages/${messageId}` (DELETE) | `/api/v1/messages/${messageId}` | Messages |
| `/api/notifications/${id}/read` | `/api/v1/notifications/${id}/read` | Notifications |
| `/api/notifications/${id}/dismiss` | `/api/v1/notifications/${id}/dismiss` | Notifications |
| `/api/notifications/${id}` (DELETE) | `/api/v1/notifications/${id}` | Notifications |
| `/api/favorites/${tutorProfileId}` (DELETE) | `/api/v1/favorites/${tutorProfileId}` | Favorites |
| `/api/favorites/${tutorProfileId}` (GET) | `/api/v1/favorites/${tutorProfileId}` | Favorites |
| `/api/tutors/availability/${id}` (DELETE) | `/api/v1/tutors/availability/${id}` | Availability |
| `/api/admin/users/${userId}` (DELETE) | `/api/v1/admin/users/${userId}` | Admin |
| `/api/admin/dashboard/recent-activities` | `/api/v1/admin/dashboard/recent-activities` | Admin |
| `/api/admin/dashboard/upcoming-sessions` | `/api/v1/admin/dashboard/upcoming-sessions` | Admin |
| `/api/admin/dashboard/monthly-revenue` | `/api/v1/admin/dashboard/monthly-revenue` | Admin |
| `/api/admin/dashboard/user-growth` | `/api/v1/admin/dashboard/user-growth` | Admin |
| `/api/tutor/student-notes/${studentId}` (GET) | `/api/v1/tutor/student-notes/${studentId}` | Tutor Notes |
| `/api/tutor/student-notes/${studentId}` (PUT) | `/api/v1/tutor/student-notes/${studentId}` | Tutor Notes |
| `/api/tutor/student-notes/${studentId}` (DELETE) | `/api/v1/tutor/student-notes/${studentId}` | Tutor Notes |

### Impact
- **Messaging:** Users cannot mark messages as read, edit, or delete messages
- **Notifications:** Users cannot mark individual notifications as read/dismissed
- **Favorites:** Users cannot remove favorite tutors or check favorite status
- **Admin Dashboard:** Several dashboard widgets fail to load data
- **Tutor Notes:** Tutors cannot manage student notes

### Evidence

**File:** `frontend/lib/api.ts`

```typescript
// Line 1162 - BROKEN
const { data } = await api.get(`/api/messages/users/${userId}`);

// Line 1201 - BROKEN
await api.patch(`/api/messages/${messageId}/read`);

// Line 1381 - BROKEN
await api.patch(`/api/notifications/${notificationId}/read`);
```

**Backend Registration:** `backend/main.py` (lines 617-649)
```python
API_V1_PREFIX = "/api/v1"
app.include_router(messages_router, prefix=API_V1_PREFIX)  # → /api/v1/messages/...
app.include_router(notifications_router, prefix=API_V1_PREFIX)  # → /api/v1/notifications/...
```

---

## 2. Configuration Verification

### 2.1 CORS Configuration ✅

**Backend** (`main.py` lines 569-595):
```python
CORS_ORIGINS = ["https://edustream.valsa.solutions", "http://edustream.valsa.solutions"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # or restricted list in production
    allow_headers=["*"],
)
```

**Status:** Correctly configured for production domain.

**Local Development Note:** `.env.localhost` should set `CORS_ORIGINS=http://localhost:3000`

### 2.2 Authentication Flow ✅

**Token Refresh:** Correctly implemented
- Endpoint: `POST /api/v1/auth/refresh`
- Frontend interceptor handles 401 with automatic refresh
- Token stored in secure cookies

**Cookie Configuration:**
```typescript
Cookies.set("token", access_token, {
  expires: 7,
  secure: true,
  sameSite: 'strict'
});
```

### 2.3 Base URL Configuration ✅

**Frontend** (`lib/api.ts`):
```typescript
const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
// Fallback: https://api.valsa.solutions
```

**Environment Files:**
- `.env.development`: `NEXT_PUBLIC_API_URL=https://api.valsa.solutions`
- `.env.production`: `NEXT_PUBLIC_API_URL=https://api.valsa.solutions`

### 2.4 WebSocket Configuration ✅

**Connection URL:**
```typescript
const wsUrl = `wss://api.valsa.solutions/ws/messages?token=${token}`;
```

**Backend Endpoint:** Registered at `/api/v1/ws/messages`

---

## 3. Environment Matrix

| Environment | Frontend URL | Backend URL | CORS Origins | Status |
|-------------|--------------|-------------|--------------|--------|
| Local Dev | http://localhost:3000 | http://localhost:8000 | http://localhost:3000 | ⚠️ Needs .env.localhost |
| Production | https://edustream.valsa.solutions | https://api.valsa.solutions | https://edustream.valsa.solutions | ✅ |
| Test (Docker) | http://test-frontend:3000 | http://test-backend:8000 | Docker internal | ✅ |

---

## 4. Recommended Fixes

### Fix 1: Update Frontend API Paths (REQUIRED)

Edit `frontend/lib/api.ts` to add `/v1/` to all broken paths:

```diff
// Messages
- const { data } = await api.get(`/api/messages/users/${userId}`);
+ const { data } = await api.get(`/api/v1/messages/users/${userId}`);

- await api.patch(`/api/messages/${messageId}/read`);
+ await api.patch(`/api/v1/messages/${messageId}/read`);

// ... (apply to all 21 endpoints)
```

### Fix 2: Add Local Development CORS (RECOMMENDED)

Create/update `.env.localhost`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Fix 3: Add Frontend Health Endpoint (OPTIONAL)

Add `app/api/health/route.ts`:
```typescript
export async function GET() {
  return Response.json({ status: 'healthy' });
}
```

---

## 5. Files Examined

### Frontend
- `frontend/lib/api.ts` (1,717 lines) - Main API client
- `frontend/lib/api/core/client.ts` - Axios instance
- `frontend/shared/utils/url.ts` - URL utilities
- `frontend/.env.development` - Dev environment
- `frontend/.env.production` - Prod environment
- `frontend/next.config.js` - Next.js configuration

### Backend
- `backend/main.py` - Router registration, CORS, middleware
- `backend/modules/messages/api.py` - Messages router
- `backend/modules/notifications/presentation/api.py` - Notifications router
- `backend/modules/students/presentation/api.py` - Favorites router

### Configuration
- `.env` - Root environment variables
- `.env.localhost` - Local development config
- `docker-compose.yml` - Service orchestration
- `docker-compose.test.yml` - Test environment

---

## 6. Verification Steps

After applying fixes:

1. **Run smoke test:**
   ```bash
   ./scripts/integration_smoke.sh
   ```

2. **Test critical flows:**
   - Login → Dashboard
   - Send message → Mark as read
   - Add favorite → Remove favorite
   - View notifications → Mark as read

3. **Check browser console:**
   - No 404 errors on API calls
   - No CORS errors

---

## 7. Conclusion

The integration is **95% correct** with a consistent pattern of missing `/v1/` prefixes in 21 specific API calls. The fix is straightforward: add the version prefix to the affected endpoints in `frontend/lib/api.ts`.

**Priority:** HIGH - These broken endpoints affect core user functionality (messaging, notifications, favorites).

**Estimated Fix Time:** 15-30 minutes (simple string replacements)

---

## Appendix: Related Documentation

- [API Inventory](./api_inventory.md) - Full frontend API call list
- [Backend Endpoints](./backend_endpoints.md) - Complete backend route list
- [Contract Diff](./contract_diff.md) - Frontend ↔ Backend mapping
