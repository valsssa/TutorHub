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

## Future Considerations

- Add refresh token rotation for longer sessions
- Consider RS256 (asymmetric) if extracting auth to microservice
- Implement token revocation list for logout

## References

- Implementation: `backend/core/security.py`
- Dependencies: `backend/core/dependencies.py`
- Configuration: `backend/core/config.py`
