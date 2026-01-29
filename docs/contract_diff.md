# Contract Diff: Frontend API Calls vs Backend Endpoints

**Generated:** 2026-01-29

This document maps frontend API calls to backend endpoints, highlighting mismatches.

---

## Legend

- ✅ **MATCH** - Frontend path matches backend route
- ❌ **MISMATCH** - Frontend path does not match backend route (will 404)
- ⚠️ **WARNING** - Potential issue or inconsistency

---

## 1. Authentication Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/auth/register` | `/api/v1/auth/register` | POST | ✅ |
| `/api/v1/auth/login` | `/api/v1/auth/login` | POST | ✅ |
| `/api/v1/auth/refresh` | `/api/v1/auth/refresh` | POST | ✅ |
| `/api/v1/auth/me` | `/api/v1/auth/me` | GET | ✅ |
| `/api/v1/auth/me` | `/api/v1/auth/me` | PUT | ✅ |
| `/api/v1/users/currency` | `/api/v1/users/currency` | PATCH | ✅ |
| `/api/v1/users/preferences` | `/api/v1/users/preferences` | PATCH | ✅ |

---

## 2. Messages Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/messages` | `/api/v1/messages` | POST | ✅ |
| `/api/v1/messages/threads` | `/api/v1/messages/threads` | GET | ✅ |
| `/api/v1/messages/search` | `/api/v1/messages/search` | GET | ✅ |
| `/api/v1/messages/unread/count` | `/api/v1/messages/unread/count` | GET | ✅ |
| `/api/messages/users/${userId}` | `/api/v1/messages/users/${userId}` | GET | ❌ **MISMATCH** |
| `/api/messages/${messageId}/read` | `/api/v1/messages/${messageId}/read` | PATCH | ❌ **MISMATCH** |
| `/api/messages/threads/${userId}/read-all` | `/api/v1/messages/threads/${userId}/read-all` | PATCH | ❌ **MISMATCH** |
| `/api/messages/${messageId}` | `/api/v1/messages/${messageId}` | PATCH | ❌ **MISMATCH** |
| `/api/messages/${messageId}` | `/api/v1/messages/${messageId}` | DELETE | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` lines 1162, 1201, 1205, 1217, 1223

---

## 3. Notifications Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/notifications` | `/api/v1/notifications` | GET | ✅ |
| `/api/v1/notifications/unread-count` | `/api/v1/notifications/unread-count` | GET | ✅ |
| `/api/v1/notifications/mark-all-read` | `/api/v1/notifications/mark-all-read` | PATCH | ✅ |
| `/api/v1/notifications/preferences` | `/api/v1/notifications/preferences` | GET | ✅ |
| `/api/v1/notifications/preferences` | `/api/v1/notifications/preferences` | PUT | ✅ |
| `/api/notifications/${id}/read` | `/api/v1/notifications/${id}/read` | PATCH | ❌ **MISMATCH** |
| `/api/notifications/${id}/dismiss` | `/api/v1/notifications/${id}/dismiss` | PATCH | ❌ **MISMATCH** |
| `/api/notifications/${id}` | `/api/v1/notifications/${id}` | DELETE | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` lines 1381, 1389, 1393, 1397

---

## 4. Favorites Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/favorites` | `/api/v1/favorites` | GET | ✅ |
| `/api/v1/favorites` | `/api/v1/favorites` | POST | ✅ |
| `/api/favorites/${tutorProfileId}` | `/api/v1/favorites/${tutorProfileId}` | DELETE | ❌ **MISMATCH** |
| `/api/favorites/${tutorProfileId}` | `/api/v1/favorites/${tutorProfileId}` | GET | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` lines 1428, 1432

---

## 5. Tutor Availability Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/tutors/availability` | `/api/v1/tutors/availability` | GET | ✅ |
| `/api/v1/tutors/availability` | `/api/v1/tutors/availability` | POST | ✅ |
| `/api/v1/tutors/availability/bulk` | `/api/v1/tutors/availability/bulk` | POST | ✅ |
| `/api/tutors/availability/${id}` | `/api/v1/tutors/availability/${id}` | DELETE | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` line 1473

---

## 6. Admin Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/v1/admin/users` | `/api/v1/admin/users` | GET | ✅ |
| `/api/v1/admin/tutors/pending` | `/api/v1/admin/tutors/pending` | GET | ✅ |
| `/api/v1/admin/tutors/approved` | `/api/v1/admin/tutors/approved` | GET | ✅ |
| `/api/v1/admin/dashboard/stats` | `/api/v1/admin/dashboard/stats` | GET | ✅ |
| `/api/v1/admin/dashboard/session-metrics` | `/api/v1/admin/dashboard/session-metrics` | GET | ✅ |
| `/api/v1/admin/dashboard/subject-distribution` | `/api/v1/admin/dashboard/subject-distribution` | GET | ✅ |
| `/api/admin/users/${userId}` | `/api/v1/admin/users/${userId}` | DELETE | ❌ **MISMATCH** |
| `/api/admin/dashboard/recent-activities` | `/api/v1/admin/dashboard/recent-activities` | GET | ❌ **MISMATCH** |
| `/api/admin/dashboard/upcoming-sessions` | `/api/v1/admin/dashboard/upcoming-sessions` | GET | ❌ **MISMATCH** |
| `/api/admin/dashboard/monthly-revenue` | `/api/v1/admin/dashboard/monthly-revenue` | GET | ❌ **MISMATCH** |
| `/api/admin/dashboard/user-growth` | `/api/v1/admin/dashboard/user-growth` | GET | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` lines 1502, 1557, 1569, 1593, 1617

---

## 7. Tutor Student Notes Endpoints

| Frontend Call | Backend Route | Method | Status |
|---------------|---------------|--------|--------|
| `/api/tutor/student-notes/${studentId}` | `/api/v1/tutor/student-notes/${studentId}` | GET | ❌ **MISMATCH** |
| `/api/tutor/student-notes/${studentId}` | `/api/v1/tutor/student-notes/${studentId}` | PUT | ❌ **MISMATCH** |
| `/api/tutor/student-notes/${studentId}` | `/api/v1/tutor/student-notes/${studentId}` | DELETE | ❌ **MISMATCH** |

**File:** `frontend/lib/api.ts` lines 1697, 1708, 1712

---

## 8. Correctly Matched Endpoints (Sample)

| Category | Frontend Call | Backend Route | Method | Status |
|----------|---------------|---------------|--------|--------|
| Subjects | `/api/v1/subjects` | `/api/v1/subjects` | GET | ✅ |
| Tutors | `/api/v1/tutors` | `/api/v1/tutors` | GET | ✅ |
| Tutors | `/api/v1/tutors/me/profile` | `/api/v1/tutors/me/profile` | GET | ✅ |
| Tutors | `/api/v1/tutors/me/about` | `/api/v1/tutors/me/about` | PATCH | ✅ |
| Tutors | `/api/v1/tutors/me/subjects` | `/api/v1/tutors/me/subjects` | PUT | ✅ |
| Bookings | `/api/v1/bookings` | `/api/v1/bookings` | GET | ✅ |
| Bookings | `/api/v1/bookings` | `/api/v1/bookings` | POST | ✅ |
| Reviews | `/api/v1/reviews` | `/api/v1/reviews` | POST | ✅ |
| Packages | `/api/v1/packages` | `/api/v1/packages` | GET | ✅ |
| Packages | `/api/v1/packages` | `/api/v1/packages` | POST | ✅ |
| Students | `/api/v1/profile/student/me` | `/api/v1/profile/student/me` | GET | ✅ |
| Students | `/api/v1/profile/student/me` | `/api/v1/profile/student/me` | PATCH | ✅ |
| Avatars | `/api/v1/users/me/avatar` | `/api/v1/users/me/avatar` | GET | ✅ |
| Avatars | `/api/v1/users/me/avatar` | `/api/v1/users/me/avatar` | POST | ✅ |
| Avatars | `/api/v1/users/me/avatar` | `/api/v1/users/me/avatar` | DELETE | ✅ |

---

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Matching | 69 | 77% |
| ❌ Mismatch | 21 | 23% |

### All Mismatched Paths (Quick Reference)

```typescript
// Messages (5 calls)
"/api/messages/users/${userId}"                    // Line 1162
"/api/messages/${messageId}/read"                  // Line 1201
"/api/messages/threads/${otherUserId}/read-all"    // Line 1205
"/api/messages/${messageId}"                       // Line 1217, 1223

// Notifications (4 calls)
"/api/notifications/${notificationId}/read"        // Line 1381, 1389
"/api/notifications/${notificationId}/dismiss"     // Line 1393
"/api/notifications/${notificationId}"             // Line 1397

// Favorites (2 calls)
"/api/favorites/${tutorProfileId}"                 // Line 1428, 1432

// Tutors Availability (1 call)
"/api/tutors/availability/${availabilityId}"       // Line 1473

// Admin (5 calls)
"/api/admin/users/${userId}"                       // Line 1502
"/api/admin/dashboard/recent-activities"           // Line 1557
"/api/admin/dashboard/upcoming-sessions"           // Line 1569
"/api/admin/dashboard/monthly-revenue"             // Line 1593
"/api/admin/dashboard/user-growth"                 // Line 1617

// Tutor Student Notes (3 calls)
"/api/tutor/student-notes/${studentId}"            // Line 1697, 1708, 1712
```

### Fix Pattern

All mismatches follow the same pattern: missing `/v1/` after `/api/`.

```diff
- "/api/messages/..."
+ "/api/v1/messages/..."

- "/api/notifications/..."
+ "/api/v1/notifications/..."

- "/api/favorites/..."
+ "/api/v1/favorites/..."

- "/api/tutors/..."
+ "/api/v1/tutors/..."

- "/api/admin/..."
+ "/api/v1/admin/..."

- "/api/tutor/..."
+ "/api/v1/tutor/..."
```
