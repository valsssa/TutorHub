# Frontend API Inventory

**Generated:** 2026-01-29
**Source:** `frontend/lib/api.ts`

This document catalogs all API calls made by the Next.js frontend.

---

## Configuration

| Setting | Value |
|---------|-------|
| Base URL | `getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL)` |
| Fallback | `https://api.valsa.solutions` |
| Timeout | 15 seconds |
| Retry | 3 attempts with exponential backoff |

---

## Authentication

### Token Storage
- Access token: Cookie `token` (secure, sameSite: strict)
- Refresh token: Cookie `refresh_token` (7-day expiry)
- Token expiry: Cookie `token_expiry`

### Auth Headers
```typescript
Authorization: Bearer ${token}
Content-Type: application/json
```

---

## API Namespaces

### 1. `auth` - Authentication (7 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user |
| POST | `/api/v1/auth/login` | No | Login (form-urlencoded) |
| POST | `/api/v1/auth/refresh` | No | Refresh access token |
| GET | `/api/v1/auth/me` | Yes | Get current user |
| PUT | `/api/v1/auth/me` | Yes | Update user profile |
| PATCH | `/api/v1/users/currency` | Yes | Update currency preference |
| PATCH | `/api/v1/users/preferences` | Yes | Update timezone |

### 2. `subjects` - Subject Catalog (1 endpoint)

| Method | Path | Auth | Cached | Description |
|--------|------|------|--------|-------------|
| GET | `/api/v1/subjects` | No | Yes (SWR) | List all subjects |

### 3. `tutors` - Tutor Profiles (15 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/tutors` | No | List tutors (paginated, filtered) |
| GET | `/api/tutors/{id}` | No | Get tutor by ID |
| GET | `/api/tutors/{id}/public` | No | Get public tutor summary |
| GET | `/api/v1/tutors/me/profile` | Tutor | Get my tutor profile |
| PATCH | `/api/v1/tutors/me/about` | Tutor | Update about section |
| PUT | `/api/v1/tutors/me/subjects` | Tutor | Replace subjects |
| PUT | `/api/v1/tutors/me/certifications` | Tutor | Replace certifications (multipart) |
| PUT | `/api/v1/tutors/me/education` | Tutor | Replace education (multipart) |
| PATCH | `/api/v1/tutors/me/description` | Tutor | Update description |
| PATCH | `/api/v1/tutors/me/video` | Tutor | Update intro video URL |
| PATCH | `/api/v1/tutors/me/pricing` | Tutor | Update pricing |
| PUT | `/api/v1/tutors/me/availability` | Tutor | Replace availability |
| POST | `/api/v1/tutors/me/submit` | Tutor | Submit for review |
| PATCH | `/api/v1/tutors/me/photo` | Tutor | Update profile photo (multipart) |
| GET | `/api/reviews/tutors/{id}` | No | Get tutor reviews |

### 4. `bookings` - Session Booking (9 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/bookings` | Yes | List bookings (filtered, paginated) |
| GET | `/api/bookings/{id}` | Yes | Get booking details |
| POST | `/api/v1/bookings` | Student | Create booking |
| POST | `/api/bookings/{id}/cancel` | Yes | Cancel booking |
| POST | `/api/bookings/{id}/reschedule` | Student | Reschedule booking |
| POST | `/api/tutor/bookings/{id}/confirm` | Tutor | Confirm booking |
| POST | `/api/tutor/bookings/{id}/decline` | Tutor | Decline booking |
| POST | `/api/tutor/bookings/{id}/mark-no-show-student` | Tutor | Mark student no-show |
| POST | `/api/tutor/bookings/{id}/mark-no-show-tutor` | Student | Mark tutor no-show |

### 5. `reviews` - Review System (1 endpoint)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/reviews` | Student | Create review |

### 6. `packages` - Session Packages (3 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/packages` | Yes | List my packages |
| POST | `/api/v1/packages` | Student | Purchase package |
| PATCH | `/api/packages/{id}/use-credit` | Student | Use package credit |

### 7. `messages` - Direct Messaging (10 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| POST | `/api/v1/messages` | Yes | Send message | ✅ |
| GET | `/api/v1/messages/threads` | Yes | List threads | ✅ |
| GET | `/api/messages/threads/{userId}` | Yes | Get thread messages | ⚠️ Missing /v1/ |
| GET | `/api/v1/messages/search` | Yes | Search messages | ✅ |
| GET | `/api/v1/messages/unread/count` | Yes | Get unread count | ✅ |
| GET | `/api/messages/users/{userId}` | Yes | Get user info | ❌ Missing /v1/ |
| PATCH | `/api/messages/{id}/read` | Yes | Mark as read | ❌ Missing /v1/ |
| PATCH | `/api/messages/threads/{userId}/read-all` | Yes | Mark thread read | ❌ Missing /v1/ |
| PATCH | `/api/messages/{id}` | Yes | Edit message | ⚠️ Check path |
| DELETE | `/api/messages/{id}` | Yes | Delete message | ❌ Missing /v1/ |

### 8. `avatars` - User Avatars (4 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/users/me/avatar` | Yes | Get avatar URL |
| POST | `/api/v1/users/me/avatar` | Yes | Upload avatar (multipart) |
| DELETE | `/api/v1/users/me/avatar` | Yes | Remove avatar |
| PATCH | `/api/admin/users/{id}/avatar` | Admin | Admin upload avatar |

### 9. `students` - Student Profile (2 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/profile/student/me` | Student | Get student profile |
| PATCH | `/api/v1/profile/student/me` | Student | Update student profile |

### 10. `notifications` - User Notifications (8 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| GET | `/api/v1/notifications` | Yes | List notifications | ✅ |
| GET | `/api/v1/notifications/unread-count` | Yes | Get unread count | ✅ |
| PATCH | `/api/v1/notifications/mark-all-read` | Yes | Mark all read | ✅ |
| GET | `/api/v1/notifications/preferences` | Yes | Get preferences | ✅ |
| PUT | `/api/v1/notifications/preferences` | Yes | Update preferences | ✅ |
| PATCH | `/api/notifications/{id}/read` | Yes | Mark as read | ❌ Missing /v1/ |
| PATCH | `/api/notifications/{id}/dismiss` | Yes | Dismiss notification | ❌ Missing /v1/ |
| DELETE | `/api/notifications/{id}` | Yes | Delete notification | ❌ Missing /v1/ |

### 11. `favorites` - Saved Tutors (4 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| GET | `/api/v1/favorites` | Student | List favorites | ✅ |
| POST | `/api/v1/favorites` | Student | Add favorite | ✅ |
| DELETE | `/api/favorites/{tutorId}` | Student | Remove favorite | ❌ Missing /v1/ |
| GET | `/api/favorites/{tutorId}` | Student | Check if favorite | ❌ Missing /v1/ |

### 12. `availability` - Tutor Schedule (5 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| GET | `/api/v1/tutors/availability` | Tutor | Get my availability | ✅ |
| POST | `/api/v1/tutors/availability` | Tutor | Create slot | ✅ |
| POST | `/api/v1/tutors/availability/bulk` | Tutor | Create bulk slots | ✅ |
| DELETE | `/api/tutors/availability/{id}` | Tutor | Delete slot | ❌ Missing /v1/ |
| GET | `/api/tutors/{id}/available-slots` | No | Get available slots | ✅ |

### 13. `admin` - Administration (14 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| GET | `/api/v1/admin/users` | Admin | List users | ✅ |
| PUT | `/api/admin/users/{id}` | Admin | Update user | ⚠️ Check path |
| DELETE | `/api/admin/users/{id}` | Admin | Delete user | ❌ Missing /v1/ |
| GET | `/api/v1/admin/tutors/pending` | Admin | Pending tutors | ✅ |
| GET | `/api/v1/admin/tutors/approved` | Admin | Approved tutors | ✅ |
| POST | `/api/admin/tutors/{id}/approve` | Admin | Approve tutor | ⚠️ Check path |
| POST | `/api/admin/tutors/{id}/reject` | Admin | Reject tutor | ⚠️ Check path |
| GET | `/api/v1/admin/dashboard/stats` | Admin | Dashboard stats | ✅ |
| GET | `/api/admin/dashboard/recent-activities` | Admin | Recent activities | ❌ Missing /v1/ |
| GET | `/api/admin/dashboard/upcoming-sessions` | Admin | Upcoming sessions | ❌ Missing /v1/ |
| GET | `/api/v1/admin/dashboard/session-metrics` | Admin | Session metrics | ✅ |
| GET | `/api/admin/dashboard/monthly-revenue` | Admin | Monthly revenue | ❌ Missing /v1/ |
| GET | `/api/v1/admin/dashboard/subject-distribution` | Admin | Subject distribution | ✅ |
| GET | `/api/admin/dashboard/user-growth` | Admin | User growth | ❌ Missing /v1/ |

### 14. `owner` - Platform Owner (5 endpoints)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/owner/dashboard` | Owner | Owner dashboard |
| GET | `/api/v1/owner/revenue` | Owner | Revenue metrics |
| GET | `/api/v1/owner/growth` | Owner | Growth metrics |
| GET | `/api/v1/owner/health` | Owner | Marketplace health |
| GET | `/api/v1/owner/commission-tiers` | Owner | Commission tiers |

### 15. `tutorStudentNotes` - Tutor Notes (3 endpoints)

| Method | Path | Auth | Description | Status |
|--------|------|------|-------------|--------|
| GET | `/api/tutor/student-notes/{studentId}` | Tutor | Get notes | ❌ Missing /v1/ |
| PUT | `/api/tutor/student-notes/{studentId}` | Tutor | Update notes | ❌ Missing /v1/ |
| DELETE | `/api/tutor/student-notes/{studentId}` | Tutor | Delete notes | ❌ Missing /v1/ |

---

## WebSocket

### Connection
```typescript
wss://api.valsa.solutions/ws/messages?token=${accessToken}
```

### Message Types (Client → Server)
- `ping` - Heartbeat
- `typing` - Typing indicator
- `message_delivered` - Delivery receipt
- `message_read` - Read receipt
- `presence_check` - Check user online status

### Message Types (Server → Client)
- `new_message` - New message received
- `message_sent` - Message send confirmation
- `delivery_receipt` - Delivery confirmation
- `message_read` - Read confirmation
- `message_edited` - Message was edited
- `message_deleted` - Message was deleted
- `typing` - User is typing
- `thread_read` - Thread marked as read

---

## Error Handling

### Retry Logic
- Max retries: 3
- Initial delay: 1000ms
- Backoff: Exponential (1s → 2s → 4s)
- Retryable: Network errors, 5xx status codes
- Non-retryable: 401, 429

### Rate Limiting (429)
- Headers parsed: `x-ratelimit-*`, `retry-after`
- Action: Browser notification, LocalStorage event
- No automatic retry

### Auth Error (401)
- Action: Attempt token refresh
- Fallback: Redirect to `/login?expired=true`

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total Endpoints | ~90 |
| Correct Paths | 69 |
| Missing /v1/ | 21 |
| Public (no auth) | ~10 |
| Cached (SWR) | ~12 |
