# Admin Dashboard Flow

This document traces the complete admin dashboard flow, including user management, tutor approval, system analytics, and platform oversight.

## Table of Contents
- [Admin Authentication](#admin-authentication)
- [Dashboard Overview](#dashboard-overview)
- [User Management Flow](#user-management-flow)
- [Tutor Approval Workflow](#tutor-approval-workflow)
- [Analytics and Metrics](#analytics-and-metrics)
- [Activity Monitoring](#activity-monitoring)

---

## Admin Authentication

### 1. Admin Login

**Same as regular authentication but with admin role validation**

**Frontend Component:** `frontend/app/(public)/login/page.tsx`

```typescript
const handleLogin = async () => {
  const token = await auth.login(email, password);
  const user = await auth.getCurrentUser();
  
  // Check role and redirect
  if (user.role === 'admin') {
    router.push('/admin');
  } else {
    router.push('/dashboard');
  }
};
```

### 2. Role-Based Access Control

**Backend Dependency:** `backend/core/dependencies.py`

**Function:** `get_current_admin_user()`

```python
def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role for endpoint access."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user
```

**Usage in Endpoints:**
```python
@router.get("/api/admin/users")
async def list_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Only accessible to admins
    pass
```

---

## Dashboard Overview

### 1. Load Dashboard

**Frontend Component:** `frontend/app/admin/page.tsx`

```typescript
useEffect(() => {
  const loadDashboard = async () => {
    // Parallel load all dashboard data
    const [stats, activities, sessions, metrics] = await Promise.all([
      admin.getDashboardStats(),
      admin.getRecentActivities(50),
      admin.getUpcomingSessions(50),
      admin.getSessionMetrics()
    ]);
    
    setStats(stats);
    setActivities(activities);
    setSessions(sessions);
    setMetrics(metrics);
  };
  
  loadDashboard();
}, []);
```

### 2. API Client Requests

**File:** `frontend/lib/api.ts` (lines 1168-1233)

**Methods:**
- `admin.getDashboardStats()` - Overview statistics
- `admin.getRecentActivities()` - Latest platform activity
- `admin.getUpcomingSessions()` - Scheduled sessions
- `admin.getSessionMetrics()` - Session completion rates
- `admin.getMonthlyRevenue()` - Revenue trends
- `admin.getSubjectDistribution()` - Popular subjects
- `admin.getUserGrowth()` - User growth over time

**Caching:**
- Stats: 30 seconds
- Activities: 15 seconds
- Sessions: 30 seconds
- Metrics: 1 minute
- Revenue: 5 minutes
- Subject distribution: 5 minutes
- User growth: 5 minutes

### 3. Dashboard Statistics Endpoint

**File:** `backend/modules/admin/presentation/api.py`

**Endpoint:** `GET /api/admin/dashboard/stats`

**Authorization:** Admin only (`Depends(get_current_admin_user)`)

**SQL Query:**
```sql
SELECT 
  -- User counts
  COUNT(*) FILTER (WHERE role = 'student') as total_students,
  COUNT(*) FILTER (WHERE role = 'tutor') as total_tutors,
  COUNT(*) FILTER (WHERE role = 'admin') as total_admins,
  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_users_this_month,
  
  -- Booking stats
  (SELECT COUNT(*) FROM bookings WHERE status = 'PENDING') as pending_bookings,
  (SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED') as confirmed_bookings,
  (SELECT COUNT(*) FROM bookings WHERE status = 'COMPLETED') as completed_bookings,
  (SELECT COUNT(*) FROM bookings WHERE status LIKE 'CANCELLED%') as cancelled_bookings,
  
  -- Tutor approval stats
  (SELECT COUNT(*) FROM tutor_profile WHERE approval_status = 'pending_approval') as pending_tutors,
  (SELECT COUNT(*) FROM tutor_profile WHERE approval_status = 'approved' AND is_verified = true) as approved_tutors,
  
  -- Revenue
  (SELECT COALESCE(SUM(total_amount), 0) FROM bookings WHERE status = 'COMPLETED') as total_revenue,
  (SELECT COALESCE(SUM(total_amount), 0) FROM bookings WHERE status = 'COMPLETED' AND created_at > NOW() - INTERVAL '30 days') as revenue_this_month,
  
  -- Active users (logged in last 7 days)
  COUNT(*) FILTER (WHERE last_login_at > NOW() - INTERVAL '7 days') as active_users
  
FROM users;
```

**Response:**
```json
{
  "total_students": 1250,
  "total_tutors": 85,
  "total_admins": 3,
  "new_users_this_month": 142,
  "pending_bookings": 23,
  "confirmed_bookings": 47,
  "completed_bookings": 3421,
  "cancelled_bookings": 234,
  "pending_tutors": 5,
  "approved_tutors": 78,
  "total_revenue": 171050.00,
  "revenue_this_month": 12340.00,
  "active_users": 567
}
```

---

## User Management Flow

### 1. List All Users

**Frontend Component:** Admin users table

```typescript
const loadUsers = async () => {
  const users = await admin.listUsers();
  setUsers(users);
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 1115-1120)

**Method:** `admin.listUsers()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/admin/users`
- **Headers:** `Authorization: Bearer <admin_token>`

### 3. Backend Returns Users

**File:** `backend/modules/admin/presentation/api.py`

**Endpoint:** `GET /api/admin/users`

**Authorization:** Admin only

**SQL Query:**
```sql
SELECT 
  u.id, u.email, u.first_name, u.last_name,
  u.role, u.is_active, u.is_verified,
  u.created_at, u.updated_at, u.last_login_at,
  u.currency, u.timezone,
  -- Student-specific data
  sp.bio as student_bio,
  sp.learning_goals,
  -- Tutor-specific data
  tp.title as tutor_title,
  tp.approval_status as tutor_approval_status,
  tp.hourly_rate as tutor_hourly_rate,
  tp.average_rating as tutor_average_rating,
  tp.total_sessions as tutor_total_sessions
FROM users u
LEFT JOIN student_profile sp ON sp.user_id = u.id
LEFT JOIN tutor_profile tp ON tp.user_id = u.id
ORDER BY u.created_at DESC;
```

**Response:**
```json
{
  "items": [
    {
      "id": 42,
      "email": "student@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "student",
      "is_active": true,
      "is_verified": true,
      "created_at": "2025-10-15T08:00:00Z",
      "last_login_at": "2025-10-21T09:30:00Z",
      "student_bio": "High school student interested in STEM"
    },
    {
      "id": 50,
      "email": "tutor@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "role": "tutor",
      "is_active": true,
      "is_verified": true,
      "tutor_approval_status": "approved",
      "tutor_hourly_rate": 50.00,
      "tutor_average_rating": 4.8,
      "tutor_total_sessions": 127
    }
  ]
}
```

### 4. Update User

**Frontend:** Edit user modal

```typescript
const handleUpdateUser = async (userId: number) => {
  const updated = await admin.updateUser(userId, {
    first_name: firstName,
    last_name: lastName,
    is_active: isActive,
    role: role  // Admin can change roles
  });
};
```

### 5. API Client Request

**File:** `frontend/lib/api.ts` (lines 1122-1126)

**Method:** `admin.updateUser()`

**HTTP Request:**
- **Method:** `PUT`
- **URL:** `/api/admin/users/42`
- **Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "role": "student"
}
```

### 6. Backend Updates User

**File:** `backend/modules/admin/presentation/api.py`

**Endpoint:** `PUT /api/admin/users/{user_id}`

**Authorization:** Admin only

**Validation:**
1. **User exists** - Verify user ID
2. **Cannot modify self** - Admin can't change own role/status
3. **Role validation** - Must be valid role (student/tutor/admin)
4. **Email unique** - If changing email, check uniqueness

**Database Operations:**
```sql
-- Update user
UPDATE users 
SET first_name = 'John',
    last_name = 'Doe',
    is_active = true,
    role = 'student',
    updated_at = NOW()
WHERE id = 42;

-- If role changed from tutor to student, handle profile
UPDATE tutor_profile 
SET approval_status = 'suspended',
    is_verified = false
WHERE user_id = 42;

-- If role changed to tutor, create profile if needed
INSERT INTO tutor_profile (user_id, approval_status, is_verified)
VALUES (42, 'draft', false)
ON CONFLICT (user_id) DO NOTHING;
```

### 7. Delete User

**Frontend:** Confirmation modal

```typescript
const handleDelete = async (userId: number) => {
  if (confirm("Are you sure? This action cannot be undone.")) {
    await admin.deleteUser(userId);
    showSuccess("User deleted successfully");
  }
};
```

### 8. API Client Request

**File:** `frontend/lib/api.ts` (lines 1128-1131)

**Method:** `admin.deleteUser()`

**HTTP Request:**
- **Method:** `DELETE`
- **URL:** `/api/admin/users/42`

### 9. Backend Deletes User

**Endpoint:** `DELETE /api/admin/users/{user_id}`

**Soft Delete Implementation:**
```sql
-- Soft delete (preferred for audit trail)
UPDATE users 
SET is_active = false,
    deleted_at = NOW(),
    deleted_by = 1,  -- Admin user ID
    email = CONCAT(email, '_deleted_', id)  -- Prevent email reuse
WHERE id = 42;

-- Or hard delete (careful - removes all data)
DELETE FROM users WHERE id = 42;
-- Cascades to: student_profile, tutor_profile, bookings, messages, reviews
```

---

## Tutor Approval Workflow

### 1. List Pending Tutors

**Frontend Component:** Admin tutor approval page

```typescript
const loadPending = async () => {
  const pending = await admin.listPendingTutors(page, pageSize);
  setPendingTutors(pending.items);
};
```

### 2. API Client Request

**File:** `frontend/lib/api.ts` (lines 1133-1138)

**Method:** `admin.listPendingTutors()`

**HTTP Request:**
- **Method:** `GET`
- **URL:** `/api/admin/tutors/pending?page=1&page_size=20`

### 3. Backend Returns Pending

**Endpoint:** `GET /api/admin/tutors/pending`

**SQL Query:**
```sql
SELECT 
  tp.id, tp.user_id, tp.title, tp.headline, tp.bio,
  tp.experience_years, tp.hourly_rate, tp.completion_percentage,
  tp.submitted_at, tp.profile_photo_url,
  u.email, u.first_name, u.last_name,
  COUNT(DISTINCT ts.id) as subject_count,
  COUNT(DISTINCT tc.id) as certification_count,
  COUNT(DISTINCT te.id) as education_count,
  STRING_AGG(DISTINCT s.name, ', ') as subjects
FROM tutor_profile tp
JOIN users u ON u.id = tp.user_id
LEFT JOIN tutor_subjects ts ON ts.tutor_profile_id = tp.id
LEFT JOIN subjects s ON s.id = ts.subject_id
LEFT JOIN tutor_certifications tc ON tc.tutor_profile_id = tp.id
LEFT JOIN tutor_education te ON te.tutor_profile_id = tp.id
WHERE tp.approval_status = 'pending_approval'
GROUP BY tp.id, u.id
ORDER BY tp.submitted_at ASC
LIMIT 20 OFFSET 0;
```

### 4. View Tutor Profile Details

**Frontend:** Click to expand full profile

Loads complete tutor profile including:
- Personal information
- Teaching experience
- Subjects and pricing
- Certifications (with document links)
- Education (with document links)
- Availability schedule
- Sample video introduction

### 5. Approve Tutor

**Frontend:** Approve button

```typescript
const handleApprove = async (tutorId: number) => {
  await admin.approveTutor(tutorId);
  showSuccess("Tutor approved!");
  refreshList();
};
```

### 6. API Client Request

**File:** `frontend/lib/api.ts` (lines 1147-1154)

**Method:** `admin.approveTutor()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/admin/tutors/10/approve`
- **Body:** `{}`

### 7. Backend Approves Tutor

**Endpoint:** `POST /api/admin/tutors/{tutor_id}/approve`

**Database Operations:**
```sql
-- Approve profile
UPDATE tutor_profile 
SET approval_status = 'approved',
    is_verified = true,
    approved_at = NOW(),
    approved_by = 1,  -- Admin user ID
    rejection_reason = NULL,
    updated_at = NOW()
WHERE id = 10;

-- Create notification
INSERT INTO notifications (
  user_id, type, title, message, link, is_read
) VALUES (
  42, 'tutor_approved',
  'Profile Approved!',
  'Congratulations! Your tutor profile is now live.',
  '/tutor/profile',
  false
);
```

**Email Notification:**
```
To: tutor@example.com
Subject: Your Tutor Profile Has Been Approved!

Hi Jane,

Great news! Your tutor profile has been reviewed and approved.
You're now visible to students and can start receiving bookings.

Next steps:
- Update your availability: https://platform.com/tutor/schedule
- Complete your profile: https://platform.com/tutor/profile
- View your public profile: https://platform.com/tutors/10

Welcome to our platform!

Best regards,
The Team
```

### 8. Reject Tutor

**Frontend:** Reject with reason

```typescript
const handleReject = async (tutorId: number) => {
  const reason = prompt("Please provide a rejection reason:");
  if (reason) {
    await admin.rejectTutor(tutorId, reason);
    showSuccess("Tutor rejected with feedback");
  }
};
```

### 9. API Client Request

**File:** `frontend/lib/api.ts` (lines 1156-1166)

**Method:** `admin.rejectTutor()`

**HTTP Request:**
- **Method:** `POST`
- **URL:** `/api/admin/tutors/10/reject`
- **Body:**
```json
{
  "rejection_reason": "Please provide verified copies of your teaching certificates. The submitted documents are not clearly legible."
}
```

### 10. Backend Rejects Tutor

**Endpoint:** `POST /api/admin/tutors/{tutor_id}/reject`

**Database Operations:**
```sql
-- Reject profile
UPDATE tutor_profile 
SET approval_status = 'rejected',
    is_verified = false,
    rejection_reason = 'Please provide verified copies...',
    rejected_at = NOW(),
    rejected_by = 1,
    updated_at = NOW()
WHERE id = 10;

-- Create notification
INSERT INTO notifications (
  user_id, type, title, message, link
) VALUES (
  42, 'tutor_rejected',
  'Profile Revision Required',
  'Your profile requires updates before approval. Click to view details.',
  '/tutor/onboarding'
);
```

**Email Notification:**
```
To: tutor@example.com
Subject: Profile Review - Action Required

Hi Jane,

Thank you for submitting your tutor profile. After review, 
we need you to make some updates before we can approve it.

Feedback:
Please provide verified copies of your teaching certificates. 
The submitted documents are not clearly legible.

What to do next:
1. Update your profile: https://platform.com/tutor/onboarding
2. Re-upload required documents
3. Resubmit for review

If you have any questions, please contact our support team.

Best regards,
The Team
```

---

## Analytics and Metrics

### 1. Session Metrics

**Endpoint:** `GET /api/admin/dashboard/session-metrics`

**SQL Query:**
```sql
SELECT 
  DATE_TRUNC('day', start_time) as date,
  COUNT(*) as total_sessions,
  COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed,
  COUNT(*) FILTER (WHERE status LIKE 'CANCELLED%') as cancelled,
  COUNT(*) FILTER (WHERE status LIKE 'NO_SHOW%') as no_shows,
  ROUND(AVG(duration_minutes), 2) as avg_duration,
  ROUND(AVG(total_amount), 2) as avg_revenue
FROM bookings
WHERE start_time > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', start_time)
ORDER BY date DESC;
```

**Response:**
```json
[
  {
    "date": "2025-10-21",
    "total_sessions": 42,
    "completed": 38,
    "cancelled": 3,
    "no_shows": 1,
    "avg_duration": 58.5,
    "avg_revenue": 52.30
  }
]
```

### 2. Monthly Revenue

**Endpoint:** `GET /api/admin/dashboard/monthly-revenue?months=6`

**SQL Query:**
```sql
SELECT 
  DATE_TRUNC('month', created_at) as month,
  COUNT(*) as booking_count,
  SUM(total_amount) as total_revenue,
  SUM(platform_fee) as platform_revenue,
  SUM(total_amount - platform_fee) as tutor_revenue,
  COUNT(DISTINCT student_id) as unique_students,
  COUNT(DISTINCT tutor_profile_id) as unique_tutors
FROM bookings
WHERE status = 'COMPLETED'
  AND created_at > NOW() - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;
```

### 3. Subject Distribution

**Endpoint:** `GET /api/admin/dashboard/subject-distribution`

**SQL Query:**
```sql
SELECT 
  s.id, s.name,
  COUNT(DISTINCT ts.tutor_profile_id) as tutor_count,
  COUNT(DISTINCT b.id) as booking_count,
  COALESCE(SUM(b.total_amount), 0) as total_revenue,
  COALESCE(AVG(r.rating), 0) as average_rating
FROM subjects s
LEFT JOIN tutor_subjects ts ON ts.subject_id = s.id
LEFT JOIN bookings b ON b.subject_id = s.id AND b.status = 'COMPLETED'
LEFT JOIN reviews r ON r.booking_id = b.id
GROUP BY s.id
ORDER BY booking_count DESC
LIMIT 20;
```

### 4. User Growth

**Endpoint:** `GET /api/admin/dashboard/user-growth?months=6`

**SQL Query:**
```sql
SELECT 
  DATE_TRUNC('month', created_at) as month,
  COUNT(*) as new_users,
  COUNT(*) FILTER (WHERE role = 'student') as new_students,
  COUNT(*) FILTER (WHERE role = 'tutor') as new_tutors,
  SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', created_at)) as cumulative_users
FROM users
WHERE created_at > NOW() - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month ASC;
```

---

## Activity Monitoring

### 1. Recent Activities

**Endpoint:** `GET /api/admin/dashboard/recent-activities?limit=50`

**SQL Query:**
```sql
SELECT 
  'booking_created' as activity_type,
  b.id as entity_id,
  b.created_at as timestamp,
  u.email as user_email,
  CONCAT('Booking #', b.id, ' created for ', s.name) as description
FROM bookings b
JOIN users u ON u.id = b.student_id
JOIN subjects s ON s.id = b.subject_id

UNION ALL

SELECT 
  'user_registered' as activity_type,
  u.id as entity_id,
  u.created_at as timestamp,
  u.email as user_email,
  CONCAT('New ', u.role, ' registered') as description
FROM users u
WHERE u.created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
  'tutor_submitted' as activity_type,
  tp.id as entity_id,
  tp.submitted_at as timestamp,
  u.email as user_email,
  'Tutor profile submitted for review' as description
FROM tutor_profile tp
JOIN users u ON u.id = tp.user_id
WHERE tp.submitted_at IS NOT NULL

ORDER BY timestamp DESC
LIMIT 50;
```

**Response:**
```json
[
  {
    "activity_type": "booking_created",
    "entity_id": 150,
    "timestamp": "2025-10-21T10:30:00Z",
    "user_email": "student@example.com",
    "description": "Booking #150 created for Mathematics"
  },
  {
    "activity_type": "user_registered",
    "entity_id": 42,
    "timestamp": "2025-10-21T09:15:00Z",
    "user_email": "newstudent@example.com",
    "description": "New student registered"
  }
]
```

### 2. Upcoming Sessions

**Endpoint:** `GET /api/admin/dashboard/upcoming-sessions?limit=50`

**SQL Query:**
```sql
SELECT 
  b.id, b.start_time, b.end_time, b.status,
  b.lesson_type, b.total_amount,
  s.name as subject_name,
  st.email as student_email,
  st.first_name as student_first_name,
  tu.email as tutor_email,
  tu.first_name as tutor_first_name,
  tp.title as tutor_title
FROM bookings b
JOIN subjects s ON s.id = b.subject_id
JOIN users st ON st.id = b.student_id
JOIN tutor_profile tp ON tp.id = b.tutor_profile_id
JOIN users tu ON tu.id = tp.user_id
WHERE b.start_time > NOW()
  AND b.status IN ('PENDING', 'CONFIRMED')
ORDER BY b.start_time ASC
LIMIT 50;
```

---

## Related Files

### Frontend
- `frontend/app/admin/page.tsx` - Main admin dashboard
- `frontend/components/dashboards/AdminDashboard.tsx` - Dashboard component
- `frontend/lib/api.ts` - Admin API methods

### Backend
- `backend/modules/admin/presentation/api.py` - Admin endpoints
- `backend/core/dependencies.py` - Admin authorization
- `backend/models.py` - All database models

### Database
- All tables (read access for analytics)
- Special focus on: `users`, `tutor_profile`, `bookings`, `reviews`
