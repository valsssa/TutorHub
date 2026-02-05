# Security Notes - Frontend-v2

## Security Audit Summary

**Date**: 2026-02-05
**Audit Type**: Automated + Manual Code Review

## Findings

### ✅ No Critical Vulnerabilities Found

#### NPM Audit Results
- **Total vulnerabilities**: 0
- **Dependencies scanned**: 680

### ✅ No `dangerouslySetInnerHTML` Usage
- No direct HTML injection risks found in the codebase

### ✅ No WebSocket/RTC Implementation
- Frontend-v2 uses REST API with polling for real-time features
- No WebSocket reconnection logic needed (not implemented)

### ✅ Environment Variables
- All client-side env vars use `NEXT_PUBLIC_` prefix correctly
- No sensitive data exposed in client bundle

## Security Considerations

### 1. Token Storage (Secure - HttpOnly Cookies)
**Current Implementation**: JWT tokens stored in HttpOnly Secure cookies

**Location**: Backend sets cookies on login/refresh; `lib/api/client.ts` sends credentials

**Security Properties**:
- **XSS Protection**: Tokens cannot be accessed by JavaScript (HttpOnly flag). Even if an attacker injects malicious JavaScript, they cannot steal the token.
- **CSRF Protection**: Double-submit cookie pattern with `X-CSRF-Token` header. Backend validates that CSRF token in header matches the csrf_token cookie.
- **Secure Transport**: Cookies only sent over HTTPS in production (Secure flag)
- **SameSite**: Cookies use `SameSite=Lax` to prevent CSRF in most scenarios

**Cookie Details**:
- `access_token`: HttpOnly Secure cookie, 15-minute TTL
- `refresh_token`: HttpOnly Secure cookie, 7-day TTL, restricted to `/api/v1/auth` path
- `csrf_token`: Readable cookie (not HttpOnly) for double-submit pattern

**Frontend Implementation**:
- No localStorage token storage (removed in Task 15)
- No sessionStorage token storage
- API client uses `credentials: 'include'` to send cookies with all requests
- Auth state determined by `/auth/me` API response
- Login/logout managed via backend cookie operations
- Token refresh automatic: API client intercepts 401 responses and calls `/auth/refresh`

**How It Works**:
1. User logs in with email/password
2. Backend validates credentials and sets HttpOnly `access_token` and `refresh_token` cookies
3. Backend also sets readable `csrf_token` cookie
4. Frontend API client automatically includes cookies with `credentials: 'include'`
5. Frontend API client extracts `csrf_token` from cookie and includes it in `X-CSRF-Token` header for unsafe methods
6. When access token expires (401), API client automatically calls `/auth/refresh` to get a new token
7. On logout, backend clears all three cookies

### 2. CORS Configuration
**Status**: ✅ Properly configured in backend
- Production origins: `https://edustream.valsa.solutions`, `https://api.valsa.solutions`
- Credentials allowed
- Strict allowed headers

### 3. API Client Security
**Features Implemented** (in `lib/api/client.ts`):
- HttpOnly cookie authentication (`credentials: 'include'` on all requests)
- CSRF token header extraction from `csrf_token` cookie via `getCsrfToken()`
- CSRF token header (`X-CSRF-Token`) added for unsafe methods (POST, PUT, PATCH, DELETE)
- Type-safe error handling with `ApiError` class
- Automatic cookie handling by browser (no manual token management)
- Automatic 401 retry with token refresh (calls `/auth/refresh` and retries original request)
- Duplicate refresh protection (only one refresh at a time)

**Code Location**:
- Client class: `lib/api/client.ts`
- Authentication hooks: `lib/hooks/use-auth.ts`
- CSRF token extraction: `getCsrfToken()` function in `lib/api/client.ts`

### 4. Route Protection
**Implementation**: Client-side route guards with auth checks
- Unauthenticated users redirected to `/login`
- Role-based access control implemented via `useIsRole` hook

## Test Coverage for Security

### Unit Tests
- `__tests__/lib/api/client.test.ts` - API client security features
- `__tests__/lib/api/auth.test.ts` - Authentication flow
- `__tests__/components/layouts/protected-route.test.tsx` - Route protection

### E2E Tests
- `e2e/integration/auth-real.spec.ts` - Real authentication against backend
- `e2e/integration/error-handling.spec.ts` - Error recovery, token expiry
- `e2e/integration/navigation-real.spec.ts` - Route protection verification

## Migration Notes - localStorage → HttpOnly Cookies

### What Was Removed (Task 15)
1. **localStorage token storage**: Previously stored `auth_token` in localStorage (vulnerable to XSS)
2. **Query client auth token handling**: Removed deprecated `localStorage.removeItem('auth_token')` from `lib/query-client.ts`
3. **E2E test token checks**: Updated tests to verify HttpOnly cookies instead of localStorage
   - `e2e/integration/auth-real.spec.ts`: Replaced localStorage.getItem checks with context.cookies()
   - `e2e/integration/error-handling.spec.ts`: Replaced localStorage.setItem with context.clearCookies()

### What Still Uses localStorage (Legitimate)
- **`lib/stores/filters-store.ts`**: UI filter state persistence (not authentication)
- **`lib/hooks/use-search.ts`**: Recent search history (not authentication)

### Backward Compatibility
- No migration needed for existing users (browser automatically handles cookies)
- Any existing localStorage tokens are ignored (backend uses cookie-based auth)
- If user previously saved tokens, they are silently disregarded

## Exempt Endpoints

The following endpoints do **not** require CSRF token protection:
- `POST /auth/login` - Initial login, no existing session
- `GET /auth/me` - Read-only, CSRF not applicable
- `POST /auth/refresh` - Token refresh, uses HttpOnly refresh_token cookie

All other unsafe methods (POST, PUT, PATCH, DELETE) require `X-CSRF-Token` header.

## Recommendations

### Immediate (Optional)
1. Add Content Security Policy meta tag in `_document.tsx` or `layout.tsx`
2. Implement rate limiting indicators in UI

### Future (Low Priority)
1. ~~Consider migrating to httpOnly cookie-based auth~~ **DONE** (Task 15)
2. ~~Add CSRF protection if using cookies~~ **DONE** (double-submit cookie pattern)
3. Implement refresh token rotation (backend-side, automatic on refresh)
4. ~~Add automatic 401 retry with token refresh~~ **DONE** (Task 12)

## Automated Security Checks

The CI pipeline includes:
- `npm audit` - Dependency vulnerability scanning
- TypeScript strict mode - Type safety
- ESLint security rules (via eslint-config-next)

To run security checks locally:
```bash
npm audit
npm run lint
npm run type-check
```
