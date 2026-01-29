# ADR-004: JWT Authentication Strategy

## Status

Accepted

## Date

2026-01-29

## Context

EduStream needs a stateless authentication mechanism that:
- Works across frontend and future mobile apps
- Doesn't require server-side session storage
- Supports role-based access control
- Integrates with OAuth providers (Google)
- Is secure against common attacks

## Decision

We will use **JWT (JSON Web Tokens)** for authentication:

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Token lifetime**: 30 minutes
- **Storage**: HttpOnly cookies with Secure and SameSite=Strict flags
- **Payload**: user_id, email, role, expiration
- **Password hashing**: bcrypt with 12 rounds

Token structure:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "student|tutor|admin|owner",
  "exp": 1706543210,
  "iat": 1706541410
}
```

## Consequences

### Positive

- **Stateless**: No server-side session storage needed
- **Scalable**: Any backend instance can validate tokens
- **Self-contained**: Role and permissions in token
- **Standard**: Widely understood, good library support
- **Mobile-ready**: Works with mobile apps

### Negative

- **No revocation**: Cannot invalidate individual tokens (without blacklist)
- **Token size**: Larger than session IDs
- **Secret key management**: Must secure and rotate secret

### Neutral

- Short token lifetime mitigates revocation issue
- Cookie storage prevents XSS token theft (vs localStorage)

## Alternatives Considered

### Option A: Server-Side Sessions

Traditional session cookies with server-side storage (Redis).

**Pros:**
- Easy revocation
- Small cookie size
- No token parsing on client

**Cons:**
- Requires session storage infrastructure
- Shared state complicates scaling
- Mobile apps need adaptation

**Why not chosen:** Adds infrastructure dependency; JWT sufficient for scale.

### Option B: OAuth 2.0 Tokens

Use OAuth 2.0 access tokens with refresh tokens.

**Pros:**
- Industry standard
- Built-in refresh mechanism
- Provider ecosystem

**Cons:**
- More complex implementation
- Overkill for first-party auth
- Requires token endpoint

**Why not chosen:** Complexity not justified for internal auth; OAuth used only for third-party (Google).

### Option C: Paseto Tokens

Modern alternative to JWT with opinionated security.

**Pros:**
- Safer defaults
- Simpler specification

**Cons:**
- Less library support
- Team unfamiliar
- Ecosystem smaller

**Why not chosen:** JWT widely understood; team familiarity more valuable.

## Refresh Token Implementation (Added 2026-01-29)

To improve user experience and security, we added refresh tokens:

### Token Lifecycle

- **Access Token**: 30 minutes (short-lived for security)
- **Refresh Token**: 7 days (long-lived for convenience)

### Flow

1. User logs in -> receives both access_token and refresh_token
2. Access token used for API requests in Authorization header
3. When access token expires (or ~5 min before), frontend uses refresh token to get new access token
4. If refresh token invalid/expired, user must re-login

### Security Measures

- Refresh tokens invalidated on password change (via `pwd_ts` claim)
- Refresh tokens invalidated on role change
- Unique `jti` claim in refresh tokens for potential revocation tracking
- Token type validation prevents using access token as refresh token
- Concurrent refresh requests handled via subscriber pattern

### Frontend Implementation

- Automatic token refresh in axios request interceptor
- Proactive refresh when token has < 5 minutes remaining
- 401 response triggers refresh attempt before failing
- Concurrent requests queue during refresh to avoid race conditions
- Cross-tab auth state sync via cookies

### Endpoints

- `POST /api/v1/auth/login`: Returns access_token + refresh_token
- `POST /api/v1/auth/refresh`: Exchanges refresh_token for new access_token

## Future Considerations

- Consider RS256 (asymmetric) if extracting auth to microservice
- Implement refresh token rotation (issue new refresh token on each refresh)
- Add token revocation list for immediate logout across all sessions
- Consider sliding session with refresh token rotation

## References

- Implementation: `backend/core/security.py`
- Dependencies: `backend/core/dependencies.py`
- Configuration: `backend/core/config.py`
