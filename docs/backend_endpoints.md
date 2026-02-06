# Backend API Endpoints

**Generated:** 2026-01-29
**Source:** `backend/main.py`, `backend/modules/*/`
**Base URL:** `https://api.valsa.solutions`
**API Version:** v1 (all endpoints under `/api/v1/`)

---

## Router Registration (main.py)

All routers are registered with `API_V1_PREFIX = "/api/v1"`:

```python
app.include_router(auth_router, prefix=API_V1_PREFIX)           # /api/v1/auth
app.include_router(oauth_router, prefix=API_V1_PREFIX)          # /api/v1/auth/google
app.include_router(password_router, prefix=API_V1_PREFIX)       # /api/v1/auth/password
app.include_router(profiles_router, prefix=API_V1_PREFIX)       # /api/v1/profile
app.include_router(students_router, prefix=API_V1_PREFIX)       # /api/v1/profile/student
app.include_router(favorites_router, prefix=API_V1_PREFIX)      # /api/v1/favorites
app.include_router(subjects_router, prefix=API_V1_PREFIX)       # /api/v1/subjects
app.include_router(bookings_router, prefix=API_V1_PREFIX)       # /api/v1/bookings
app.include_router(reviews_router, prefix=API_V1_PREFIX)        # /api/v1/reviews
app.include_router(messages_router, prefix=API_V1_PREFIX)       # /api/v1/messages
app.include_router(notifications_router, prefix=API_V1_PREFIX)  # /api/v1/notifications
app.include_router(packages_router, prefix=API_V1_PREFIX)       # /api/v1/packages
app.include_router(payments_router, prefix=API_V1_PREFIX)       # /api/v1/payments
app.include_router(wallet_router, prefix=API_V1_PREFIX)         # /api/v1/wallet
app.include_router(admin_router, prefix=API_V1_PREFIX)          # /api/v1/admin
app.include_router(owner_router, prefix=API_V1_PREFIX)          # /api/v1/owner
app.include_router(tutor_profile_router, prefix=API_V1_PREFIX)  # /api/v1/tutors
app.include_router(availability_router, prefix=API_V1_PREFIX)   # /api/v1/tutors/availability
app.include_router(student_notes_router, prefix=API_V1_PREFIX)  # /api/v1/tutor/student-notes
app.include_router(websocket_router, prefix=API_V1_PREFIX)      # /api/v1/ws
```

---

## Endpoint Categories

### 1. Health & System

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/health` | No | System health check |
| GET | `/docs` | No | Swagger UI documentation |
| GET | `/redoc` | No | ReDoc documentation |
| GET | `/openapi.json` | No | OpenAPI spec |

### 2. Authentication (`/api/v1/auth`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user |
| POST | `/api/v1/auth/login` | No | Login (form-urlencoded) |
| POST | `/api/v1/auth/refresh` | No | Refresh access token |
| GET | `/api/v1/auth/me` | Yes | Get current user |
| PUT | `/api/v1/auth/me` | Yes | Update current user |
| GET | `/api/v1/auth/google/login` | No | Google OAuth URL |
| GET | `/api/v1/auth/google/callback` | No | Google OAuth callback |
| POST | `/api/v1/auth/google/link` | Yes | Link Google account |
| DELETE | `/api/v1/auth/google/unlink` | Yes | Unlink Google account |
| POST | `/api/v1/auth/password/reset-request` | No | Request password reset |
| POST | `/api/v1/auth/password/verify-token` | No | Verify reset token |
| POST | `/api/v1/auth/password/reset-confirm` | No | Confirm password reset |

### 3. Subjects (`/api/v1/subjects`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/subjects` | No | List all subjects |
| POST | `/api/v1/subjects` | Admin | Create subject |
| PUT | `/api/v1/subjects/{id}` | Admin | Update subject |
| DELETE | `/api/v1/subjects/{id}` | Admin | Delete subject |

### 4. Tutors (`/api/v1/tutors`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/tutors` | No | List tutors (paginated) |
| GET | `/api/v1/tutors/{id}` | No | Get tutor profile |
| GET | `/api/v1/tutors/{id}/public` | No | Get public summary |
| GET | `/api/v1/tutors/{id}/available-slots` | No | Get available slots |
| GET | `/api/v1/tutors/me/profile` | Tutor | Get my profile |
| PATCH | `/api/v1/tutors/me/about` | Tutor | Update about |
| PUT | `/api/v1/tutors/me/subjects` | Tutor | Replace subjects |
| PUT | `/api/v1/tutors/me/certifications` | Tutor | Replace certifications |
| PUT | `/api/v1/tutors/me/education` | Tutor | Replace education |
| PATCH | `/api/v1/tutors/me/description` | Tutor | Update description |
| PATCH | `/api/v1/tutors/me/video` | Tutor | Update video URL |
| PATCH | `/api/v1/tutors/me/pricing` | Tutor | Update pricing |
| PUT | `/api/v1/tutors/me/availability` | Tutor | Replace availability |
| POST | `/api/v1/tutors/me/submit` | Tutor | Submit for review |
| PATCH | `/api/v1/tutors/me/photo` | Tutor | Update photo |

### 5. Tutor Availability (`/api/v1/tutors/availability`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/tutors/availability` | Tutor | Get my availability |
| POST | `/api/v1/tutors/availability` | Tutor | Create slot |
| DELETE | `/api/v1/tutors/availability/{id}` | Tutor | Delete slot |
| POST | `/api/v1/tutors/availability/bulk` | Tutor | Create bulk slots |

### 6. Bookings (`/api/v1/bookings`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/bookings` | Yes | List bookings |
| GET | `/api/v1/bookings/{id}` | Yes | Get booking |
| POST | `/api/v1/bookings` | Student | Create booking |
| POST | `/api/v1/bookings/{id}/cancel` | Yes | Cancel booking |
| POST | `/api/v1/bookings/{id}/reschedule` | Student | Reschedule booking |
| POST | `/api/v1/tutor/bookings/{id}/confirm` | Tutor | Confirm booking |
| POST | `/api/v1/tutor/bookings/{id}/decline` | Tutor | Decline booking |
| POST | `/api/v1/tutor/bookings/{id}/mark-no-show-student` | Tutor | Mark student no-show |
| POST | `/api/v1/tutor/bookings/{id}/mark-no-show-tutor` | Student | Mark tutor no-show |
| POST | `/api/v1/bookings/{id}/dispute` | Yes | Open dispute |
| POST | `/api/v1/bookings/{id}/regenerate-meeting` | Yes | Regenerate Zoom link |

### 7. Reviews (`/api/v1/reviews`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| POST | `/api/v1/reviews` | Student | Create review |
| GET | `/api/v1/reviews/tutors/{tutor_id}` | No | Get tutor reviews |

### 8. Packages (`/api/v1/packages`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/packages` | Yes | List my packages |
| POST | `/api/v1/packages` | Student | Purchase package |
| PATCH | `/api/v1/packages/{id}/use-credit` | Student | Use package credit |

### 9. Messages (`/api/v1/messages`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| POST | `/api/v1/messages` | Yes | Send message |
| GET | `/api/v1/messages/threads` | Yes | List threads |
| GET | `/api/v1/messages/threads/{user_id}` | Yes | Get thread messages |
| GET | `/api/v1/messages/search` | Yes | Search messages |
| GET | `/api/v1/messages/unread/count` | Yes | Get unread count |
| GET | `/api/v1/messages/users/{user_id}` | Yes | Get user info |
| PATCH | `/api/v1/messages/{id}/read` | Yes | Mark as read |
| PATCH | `/api/v1/messages/threads/{user_id}/read-all` | Yes | Mark thread read |
| PATCH | `/api/v1/messages/{id}` | Yes | Edit message |
| DELETE | `/api/v1/messages/{id}` | Yes | Delete message |
| POST | `/api/v1/messages/with-attachment` | Yes | Send with attachment |
| GET | `/api/v1/messages/attachments/{id}/download` | Yes | Download attachment |

### 10. Notifications (`/api/v1/notifications`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/notifications` | Yes | List notifications |
| GET | `/api/v1/notifications/unread-count` | Yes | Get unread count |
| PATCH | `/api/v1/notifications/{id}/read` | Yes | Mark as read |
| PATCH | `/api/v1/notifications/mark-all-read` | Yes | Mark all read |
| PATCH | `/api/v1/notifications/{id}/dismiss` | Yes | Dismiss notification |
| DELETE | `/api/v1/notifications/{id}` | Yes | Delete notification |
| GET | `/api/v1/notifications/preferences` | Yes | Get preferences |
| PUT | `/api/v1/notifications/preferences` | Yes | Update preferences |

### 11. Favorites (`/api/v1/favorites`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/favorites` | Student | List favorites |
| POST | `/api/v1/favorites` | Student | Add favorite |
| DELETE | `/api/v1/favorites/{tutor_id}` | Student | Remove favorite |
| GET | `/api/v1/favorites/{tutor_id}` | Student | Check favorite |

### 12. User Management (`/api/v1/users`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/users/me/avatar` | Yes | Get avatar URL |
| POST | `/api/v1/users/me/avatar` | Yes | Upload avatar |
| DELETE | `/api/v1/users/me/avatar` | Yes | Remove avatar |
| GET | `/api/v1/users/preferences` | Yes | Get preferences |
| PUT | `/api/v1/users/preferences` | Yes | Update preferences |
| GET | `/api/v1/users/currency` | Yes | Get currency |
| PUT | `/api/v1/users/currency` | Yes | Update currency |

### 13. Student Profile (`/api/v1/profile/student`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/profile/student/me` | Student | Get profile |
| PATCH | `/api/v1/profile/student/me` | Student | Update profile |

### 14. Tutor Student Notes (`/api/v1/tutor/student-notes`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/tutor/student-notes/{student_id}` | Tutor | Get notes |
| PUT | `/api/v1/tutor/student-notes/{student_id}` | Tutor | Update notes |
| DELETE | `/api/v1/tutor/student-notes/{student_id}` | Tutor | Delete notes |

### 15. Admin (`/api/v1/admin`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/admin/users` | Admin | List users |
| PUT | `/api/v1/admin/users/{id}` | Admin | Update user |
| DELETE | `/api/v1/admin/users/{id}` | Admin | Delete user |
| PATCH | `/api/v1/admin/users/{id}/avatar` | Admin | Update user avatar |
| GET | `/api/v1/admin/tutors/pending` | Admin | Pending tutors |
| GET | `/api/v1/admin/tutors/approved` | Admin | Approved tutors |
| POST | `/api/v1/admin/tutors/{id}/approve` | Admin | Approve tutor |
| POST | `/api/v1/admin/tutors/{id}/reject` | Admin | Reject tutor |
| GET | `/api/v1/admin/dashboard/stats` | Admin | Dashboard stats |
| GET | `/api/v1/admin/dashboard/recent-activities` | Admin | Recent activities |
| GET | `/api/v1/admin/dashboard/upcoming-sessions` | Admin | Upcoming sessions |
| GET | `/api/v1/admin/dashboard/session-metrics` | Admin | Session metrics |
| GET | `/api/v1/admin/dashboard/monthly-revenue` | Admin | Monthly revenue |
| GET | `/api/v1/admin/dashboard/subject-distribution` | Admin | Subject distribution |
| GET | `/api/v1/admin/dashboard/user-growth` | Admin | User growth |

### 16. Owner (`/api/v1/owner`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| GET | `/api/v1/owner/dashboard` | Owner | Owner dashboard |
| GET | `/api/v1/owner/revenue` | Owner | Revenue metrics |
| GET | `/api/v1/owner/growth` | Owner | Growth metrics |
| GET | `/api/v1/owner/health` | Owner | Marketplace health |
| GET | `/api/v1/owner/commission-tiers` | Owner | Commission tiers |

### 17. Payments (`/api/v1/payments`, `/api/v1/wallet`)

| Method | Full Path | Auth | Description |
|--------|-----------|------|-------------|
| POST | `/api/v1/payments/checkout` | Student | Create checkout |
| GET | `/api/v1/payments/status/{booking_id}` | Yes | Payment status |
| POST | `/api/v1/payments/refund` | Admin | Process refund |
| POST | `/api/v1/payments/webhook` | No | Stripe webhook |
| GET | `/api/v1/wallet/balance` | Yes | Get balance |
| GET | `/api/v1/wallet/transactions` | Yes | List transactions |
| POST | `/api/v1/wallet/withdraw` | Tutor | Request withdrawal |

### 18. WebSocket (`/api/v1/ws`)

| Path | Auth | Description |
|------|------|-------------|
| `/api/v1/ws/messages?token={token}` | Token query param | Real-time messaging |

---

## CORS Configuration

```python
allow_origins = ["https://edustream.valsa.solutions", "http://edustream.valsa.solutions"]
allow_credentials = True
allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
allow_headers = ["Authorization", "Content-Type", "Accept"]
max_age = 600
```

---

## Authentication

**Type:** JWT Bearer Token

**Header:** `Authorization: Bearer <access_token>`

**Token Expiry:**
- Access: 30 minutes
- Refresh: 7 days

**Cookie Security:**
- Secure: true
- SameSite: strict

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Registration | 5/minute |
| Login | 10/minute |
| Refresh | 30/minute |
| Standard GET | 60/minute |
| Standard POST | 10-30/minute |

---

## Response Format

**Success:**
```json
{
  "data": { ... }
}
```

**Error:**
```json
{
  "detail": "Error message"
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```
