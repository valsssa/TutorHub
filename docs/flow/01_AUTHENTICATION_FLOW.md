# Authentication Flow

This document traces the complete authentication flow from frontend to backend, including registration, login, and session management.

## Table of Contents
- [Registration Flow](#registration-flow)
- [Login Flow](#login-flow)
- [Get Current User Flow](#get-current-user-flow)
- [Logout Flow](#logout-flow)

---

## Registration Flow

### 1. User Submits Registration Form

**Frontend Component:** `frontend/app/(public)/register/page.tsx`

```typescript
// User fills form and clicks register
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Call auth.register() from API client
  const user = await auth.register(
    email,
    password,
    firstName,
    lastName,
    "student", // default role
    timezone,
    currency
  );
}
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 365-391)

**Method:** `auth.register()`

```typescript
async register(
  email: string,
  password: string,
  first_name: string,
  last_name: string,
  role: string = "student",
  timezone?: string,
  currency?: string,
): Promise<User>
```

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/auth/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "email": "student@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "timezone": "UTC",
  "currency": "USD"
}
```

### 3. Backend Receives Request

**File:** `backend/modules/auth/presentation/api.py` (lines 33-134)

**Endpoint:** `POST /api/auth/register`

**Rate Limit:** 5 requests/minute per IP

**Handler Function:** `register()`

**Dependencies:**
- `Request` - FastAPI request object
- `UserCreate` - Pydantic schema for validation
- `AuthService` - Business logic service

### 4. Request Validation

**File:** `backend/schemas.py`

**Schema:** `UserCreate`

Validates:
- Email: max 254 chars, valid RFC 5322 format, lowercase normalization
- Password: 6-128 characters
- Role: must be 'student', 'tutor', or 'admin'
- Names: required strings

### 5. Service Layer Processing

**File:** `backend/modules/auth/application/services.py`

**Method:** `AuthService.register_user()`

**Business Logic:**
1. **Email normalization** - converts to lowercase, strips whitespace
2. **Duplicate check** - queries database for existing email
3. **Password hashing** - bcrypt with 12 rounds
4. **User creation** - creates User record in database
5. **Profile creation** - creates StudentProfile or TutorProfile based on role
6. **Default preferences** - sets currency (USD) and timezone (UTC)
7. **JWT token generation** - creates access token for immediate login

**Database Operations:**
```sql
-- Insert user
INSERT INTO users (email, hashed_password, role, first_name, last_name, currency, timezone, is_active, is_verified)
VALUES ('student@example.com', '$2b$12$...', 'student', 'John', 'Doe', 'USD', 'UTC', true, false);

-- Insert profile (if student)
INSERT INTO student_profile (user_id) VALUES (42);
```

### 6. Response Generation

**File:** `backend/modules/auth/presentation/api.py` (lines 120-133)

**Response Schema:** `UserResponse`

```json
{
  "id": 42,
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-21T10:30:00.000Z",
  "updated_at": "2025-10-21T10:30:00.000Z",
  "avatar_url": "https://api.valsa.solutions/api/avatars/default.png",
  "currency": "USD",
  "timezone": "UTC"
}
```

### 7. Frontend Handles Response

**File:** `frontend/lib/api.ts` (lines 386-390)

- Normalizes user object (handles snake_case to camelCase)
- Returns user data to component
- Component redirects to dashboard or shows success message

---

## Login Flow

### 1. User Submits Login Form

**Frontend Component:** `frontend/app/(public)/login/page.tsx`

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Call auth.login() from API client
  const token = await auth.login(email, password);
  
  // Get user profile after login
  const user = await auth.getCurrentUser();
  
  // Redirect based on role
  router.push('/dashboard');
}
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 393-424)

**Method:** `auth.login()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/auth/login`
- **Headers:** `Content-Type: application/x-www-form-urlencoded`
- **Body:** `username=student@example.com&password=securepassword`

**Note:** Uses OAuth2 form format (username/password fields)

### 3. Backend Authenticates

**File:** `backend/modules/auth/presentation/api.py` (lines 136-214)

**Endpoint:** `POST /api/auth/login`

**Rate Limit:** 10 requests/minute per IP

**Handler Function:** `login()`

**Dependencies:**
- `OAuth2PasswordRequestForm` - FastAPI OAuth2 form parser
- `AuthService` - Authentication service

### 4. Service Layer Authentication

**File:** `backend/modules/auth/application/services.py`

**Method:** `AuthService.authenticate_user()`

**Process:**
1. **Email lookup** - case-insensitive search using indexed `LOWER(email)`
2. **User existence check** - 401 if not found
3. **Password verification** - bcrypt constant-time comparison
4. **Account status check** - 403 if inactive or not verified
5. **JWT token generation** - 30-minute expiry

**Security:**
- Constant-time password comparison prevents timing attacks
- Failed attempts logged for security monitoring
- Rate limiting prevents brute force attacks

### 5. JWT Token Generation

**File:** `backend/core/auth.py`

**Function:** `create_access_token()`

**Token Payload:**
```json
{
  "sub": "student@example.com",
  "user_id": 42,
  "role": "student",
  "exp": 1698768600  // 30 minutes from now
}
```

**Algorithm:** HS256 (HMAC SHA-256)

### 6. Response and Cookie Storage

**Backend Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Frontend Storage:** `frontend/lib/api.ts` (lines 409-413)

```typescript
Cookies.set("token", data.access_token, {
  expires: 7,        // 7 days
  secure: true,      // HTTPS only
  sameSite: 'strict' // CSRF protection
});
```

### 7. Cache Clearance

**File:** `frontend/lib/api.ts` (line 416)

Clears all cached API responses on login to ensure fresh data.

---

## Get Current User Flow

### 1. Component Requests User Data

**Usage Pattern:** Every protected page on mount

```typescript
useEffect(() => {
  const fetchUser = async () => {
    const user = await auth.getCurrentUser();
    setUser(user);
  };
  fetchUser();
}, []);
```

### 2. API Client Sends Request

**File:** `frontend/lib/api.ts` (lines 426-436)

**Method:** `auth.getCurrentUser()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/auth/me`
- **Headers:** `Authorization: Bearer <token>`

**Note:** Token automatically added by axios interceptor (lines 279-288)

### 3. Backend Validates Token

**File:** `backend/core/dependencies.py`

**Dependency:** `get_current_user()`

**Process:**
1. **Extract token** - from Authorization header
2. **Decode JWT** - validates signature and expiration
3. **Load user** - queries database by user_id from token claims
4. **Check status** - verifies user is active
5. **Return user** - passes to endpoint handler

**Security:**
- Token signature validation prevents tampering
- Expiration check ensures fresh sessions
- User status check prevents access by deactivated accounts

### 4. Endpoint Returns User Data

**File:** `backend/modules/auth/presentation/api.py` (lines 216-293)

**Endpoint:** `GET /api/auth/me`

**Handler Function:** `get_me()`

**Process:**
1. Receives current user from dependency injection
2. Fetches avatar URL from AvatarService
3. Constructs UserResponse with all user data

**Response:**
```json
{
  "id": 42,
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-10-15T08:00:00.000Z",
  "updated_at": "2025-10-21T10:30:00.000Z",
  "avatar_url": "https://api.valsa.solutions/api/avatars/42.jpg",
  "currency": "EUR",
  "timezone": "Europe/Paris"
}
```

### 5. Frontend Normalizes Response

**File:** `frontend/lib/api.ts` (line 431)

```typescript
return normalizeUser(data);
```

Converts snake_case fields to camelCase and handles avatar URL variations.

---

## Logout Flow

### 1. User Clicks Logout

**Frontend Component:** Navigation bar, user menu, etc.

```typescript
const handleLogout = () => {
  auth.logout();
};
```

### 2. API Client Clears Session

**File:** `frontend/lib/api.ts` (lines 438-445)

**Method:** `auth.logout()`

**Process:**
1. **Remove token cookie** - `Cookies.remove("token")`
2. **Clear cache** - removes all cached API responses
3. **Redirect to home** - `window.location.href = "/"`

**Note:** No backend API call required (JWT is stateless)

### 3. Automatic Cleanup

**Interceptor:** `frontend/lib/api.ts` (lines 290-320)

If any API call returns 401 (Unauthorized):
1. Automatically removes token cookie
2. Redirects to login page
3. Prevents further authenticated requests

---

## Error Handling

### Common Error Responses

**400 Bad Request**
- Invalid email format
- Password too short/long
- Missing required fields

**401 Unauthorized**
- Invalid credentials
- Token expired
- Token invalid/tampered

**403 Forbidden**
- Account inactive
- Account not verified
- Insufficient permissions

**409 Conflict**
- Email already registered

**429 Too Many Requests**
- Rate limit exceeded
- Registration: 5/min
- Login: 10/min

---

## Security Features

### Password Security
- **Hashing:** bcrypt with 12 rounds
- **Validation:** 6-128 characters
- **Comparison:** Constant-time to prevent timing attacks

### Token Security
- **Algorithm:** HS256 (HMAC SHA-256)
- **Expiry:** 30 minutes
- **Storage:** Secure, SameSite cookies
- **Transmission:** HTTPS only

### Rate Limiting
- **Registration:** 5 attempts/minute per IP
- **Login:** 10 attempts/minute per IP
- **General API:** 20 requests/minute per IP

### Input Validation
- **Email:** RFC 5322 format, max 254 chars
- **Password:** Length validation, no plaintext storage
- **Role:** Enum validation, default to 'student'

---

## Related Files

### Frontend
- `frontend/app/(public)/login/page.tsx` - Login page component
- `frontend/app/(public)/register/page.tsx` - Registration page component
- `frontend/lib/api.ts` - API client with auth methods
- `frontend/types/index.ts` - TypeScript type definitions

### Backend
- `backend/modules/auth/presentation/api.py` - Auth endpoints
- `backend/modules/auth/application/services.py` - Auth business logic
- `backend/core/auth.py` - JWT token utilities
- `backend/core/dependencies.py` - Authentication dependencies
- `backend/schemas.py` - Pydantic validation schemas
- `backend/models.py` - User database model

### Database
- `database/init.sql` - User table schema
- `database/migrations/` - Schema migrations
