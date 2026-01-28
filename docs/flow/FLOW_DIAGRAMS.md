# Platform Flow Diagrams - Quick Reference

This document provides simplified flow diagrams for all major platform features. For detailed documentation with code examples and database queries, see the individual flow documents.

---

## 🔐 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

Registration:
User → Register Form → API Client (auth.register) → Backend Validation
→ Hash Password (bcrypt 12 rounds) → Create User + Profile → JWT Token
→ Store in Cookie → Redirect to Dashboard

Login:
User → Login Form → API Client (auth.login) → Backend Auth
→ Verify Password (constant-time) → Generate JWT (30min) → Cookie
→ Fetch User Profile → Redirect by Role

Get Current User:
Component → API Client (auth.getCurrentUser) → Backend JWT Validation
→ Decode Token → Load User from DB → Return Profile + Avatar

Logout:
User → Logout Button → Remove Cookie → Clear Cache → Redirect to Home
```

**Key Files:**
- Frontend: `frontend/app/(public)/login/page.tsx`, `frontend/app/(public)/register/page.tsx`
- Backend: `backend/modules/auth/presentation/api.py`
- API: `frontend/lib/api.ts` (lines 364-491)

[📖 Full Documentation](./01_AUTHENTICATION_FLOW.md)

---

## 📅 Booking Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        BOOKING FLOW                              │
└─────────────────────────────────────────────────────────────────┘

Create Booking:
Student → Search Tutors → View Profile → Select Time Slot
→ API Client (bookings.create) → Backend Service
→ Validate Availability → Check Conflicts → Calculate Price
→ Deduct Package Credit (if used) → Create Booking (PENDING/CONFIRMED)
→ Generate Join URL → Notify Tutor

Confirm Booking (Tutor):
Tutor → View Pending → Click Confirm → API Client (bookings.confirm)
→ Backend Update Status (CONFIRMED) → Generate Join URL
→ Notify Student → Update Dashboard

Cancel Booking:
User → Click Cancel → API Client (bookings.cancel)
→ Backend Policy Check (12h rule) → Determine Refund
→ Update Status (CANCELLED_BY_STUDENT/TUTOR) → Restore Credits
→ Notify Participants

Reschedule:
Student → Request New Time → API Client (bookings.reschedule)
→ Backend Policy Validation (≥12h before) → Check New Time Conflicts
→ Update Times → Add Note → Notify Tutor

No-Show:
Tutor/Student → Report No-Show (10min+ after start, <24h)
→ API Client (markStudentNoShow/markTutorNoShow)
→ Backend Validation → Update Status → Process Payment/Refund
→ Update Metrics

Review:
Student → Submit Review → API Client (reviews.create)
→ Backend Validation (booking completed, no duplicate)
→ Create Review → Update Tutor Rating → Clear Cache
```

**Key Files:**
- Frontend: `frontend/app/tutors/[id]/book/page.tsx`, `frontend/app/bookings/page.tsx`
- Backend: `backend/modules/bookings/presentation/api.py`, `backend/modules/bookings/service.py`
- API: `frontend/lib/api.ts` (lines 719-831)

[📖 Full Documentation](./02_BOOKING_FLOW.md)

---

## 💬 Messaging Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       MESSAGING FLOW                             │
└─────────────────────────────────────────────────────────────────┘

Send Message:
User → Compose Message → API Client (messages.send)
→ Backend Service → Validate Participants → Mask PII (if pre-booking)
→ Insert Message → WebSocket Broadcast to Recipient
→ WebSocket Sync to Sender (multi-device) → Update UI

Real-Time Delivery:
Frontend → Establish WebSocket Connection (with JWT)
→ Backend Accept & Store Connection → Listen for Events
→ Receive Message Event → Update Chat UI → Auto-mark Read (if focused)

Thread Management:
Component → Load Threads → API Client (messages.listThreads)
→ Backend Query (latest messages, unread counts) → Return List
→ User Clicks Thread → Load Conversation (messages.getThreadMessages)
→ Backend Paginated Query → Return Messages (chronological)

File Attachment:
User → Select File → API Client (POST /api/messages/with-attachment)
→ Backend Validate (size, type) → Upload to S3/MinIO (private bucket)
→ Create Attachment Record → Send Message → WebSocket Notify
→ User Downloads → Generate Presigned URL (1h expiry) → Open File

Read Receipt:
Message Visible → API Client (messages.markRead)
→ Backend Update (is_read=true, read_at=NOW())
→ WebSocket Notify Sender (message_read event) → Update UI

Edit/Delete:
User → Edit Message (within 15min) → API Client (messages.editMessage)
→ Backend Validate Ownership & Time → Update Content (is_edited=true)
→ WebSocket Notify → Update UI

User → Delete Message → API Client (messages.deleteMessage)
→ Backend Soft Delete (deleted_at, deleted_by) → WebSocket Notify
→ Remove from UI
```

**Key Files:**
- Frontend: `frontend/app/messages/page.tsx`, `frontend/hooks/useWebSocket.ts`
- Backend: `backend/modules/messages/api.py`, `backend/modules/messages/websocket.py`
- API: `frontend/lib/api.ts` (lines 869-970)

[📖 Full Documentation](./03_MESSAGING_FLOW.md)

---

## 👨‍🏫 Tutor Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   TUTOR ONBOARDING FLOW                          │
└─────────────────────────────────────────────────────────────────┘

Register as Tutor:
User → Register (role="tutor") → Backend Create User + TutorProfile
→ Profile Status: "draft", Completion: 0%

Step 1: Personal Info:
Tutor → Fill About Section (title, headline, bio, experience, languages)
→ API Client (tutors.updateAbout) → Backend Validate & Update
→ Recalculate Completion %

Step 2: Subjects & Pricing:
Tutor → Select Subjects + Set Rates → API Client (tutors.replaceSubjects)
→ Backend Delete Old → Insert New → Update Base Rate
→ Optional: Add Package Deals (tutors.updatePricing)

Step 3: Documents:
Tutor → Upload Certifications (with files)
→ API Client (tutors.replaceCertifications) → Backend Parse FormData
→ Upload Files to S3 → Generate Presigned URLs → Insert Records
→ Similar for Education (tutors.replaceEducation)

Step 4: Availability:
Tutor → Configure Weekly Schedule → API Client (tutors.replaceAvailability)
→ Backend Validate (no overlaps, valid times) → Delete Old → Insert New
→ Store Timezone

Step 5: Submit:
Tutor → Review & Submit → API Client (tutors.submitForReview)
→ Backend Validate (≥80% complete, required sections)
→ Update Status: "pending_approval" → Notify Admins

Admin Review:
Admin → View Pending List (admin.listPendingTutors)
→ Review Profile (documents, experience, subjects)
→ Decision: Approve or Reject

  Approve:
  Admin → Click Approve (admin.approveTutor)
  → Backend Update (status="approved", is_verified=true)
  → Notify Tutor → Profile Goes Live

  Reject:
  Admin → Provide Reason (admin.rejectTutor)
  → Backend Update (status="rejected", rejection_reason)
  → Notify Tutor → Tutor Can Revise & Resubmit
```

**Key Files:**
- Frontend: `frontend/app/tutor/onboarding/page.tsx`, `frontend/app/tutor/profile/page.tsx`
- Backend: `backend/modules/tutor_profile/presentation/api.py`, `backend/modules/admin/presentation/api.py`
- API: `frontend/lib/api.ts` (lines 566-711, 1147-1166)

[📖 Full Documentation](./04_TUTOR_ONBOARDING_FLOW.md)

---

## 👨‍🎓 Student Profile Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    STUDENT PROFILE FLOW                          │
└─────────────────────────────────────────────────────────────────┘

Profile Creation:
User → Register (role="student") → Backend Create User + StudentProfile
→ Profile Created (all fields optional)

Update Profile:
Student → Edit Profile (bio, learning_goals, preferred_style, interests)
→ API Client (students.updateProfile) → Backend Validate & Update

Favorites Management:
Student → Browse Tutors → Click "Add to Favorites"
→ API Client (favorites.addFavorite) → Backend Validate (tutor approved)
→ Insert Favorite Record → Show Success

Student → View Saved Tutors (favorites.getFavorites)
→ Backend Query (with tutor details) → Return List

Student → Remove Favorite → API Client (favorites.removeFavorite)
→ Backend Delete Record

Package Purchase:
Student → View Tutor Packages → Select Package
→ Stripe Checkout → Payment Complete
→ API Client (packages.purchase with payment_intent_id)
→ Backend Verify Payment → Create Package Record (active, full credits)
→ Set Expiration (3 months)

Use Package Credit:
Student → Book Session with Package → API Client (bookings.create)
→ Backend Deduct Credit (remaining_credits - 1)
→ If credits=0, Mark Package "used"

Package Expiration:
Background Job (daily) → Check Expired Packages
→ Update Status: "expired" → Notify Students

Learning Preferences:
Student → Update Preferences (timezone, currency, notification settings)
→ API Client (auth.updatePreferences) → Backend Update User Record
→ All Prices/Times Display in User Preferences
```

**Key Files:**
- Frontend: `frontend/app/profile/page.tsx`, `frontend/app/saved-tutors/page.tsx`
- Backend: `backend/modules/students/presentation/api.py`, `backend/modules/packages/presentation/api.py`
- API: `frontend/lib/api.ts` (lines 837-863, 1024-1113)

[📖 Full Documentation](./05_STUDENT_PROFILE_FLOW.md)

---

## 🛠️ Admin Dashboard Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   ADMIN DASHBOARD FLOW                           │
└─────────────────────────────────────────────────────────────────┘

Admin Login:
Admin → Login → Backend Verify Role="admin"
→ Redirect to /admin Dashboard

Dashboard Load:
Component → Parallel Load:
  - admin.getDashboardStats() (users, bookings, revenue)
  - admin.getRecentActivities() (latest actions)
  - admin.getUpcomingSessions() (scheduled bookings)
  - admin.getSessionMetrics() (completion rates)
  - admin.getMonthlyRevenue() (revenue trends)
  - admin.getSubjectDistribution() (popular subjects)
  - admin.getUserGrowth() (registration trends)
→ Backend Complex Queries (aggregations, joins)
→ Return Analytics Data → Display Charts & Stats

User Management:
Admin → View Users List (admin.listUsers)
→ Backend Query All Users (with profile data) → Return List

Admin → Edit User → Update Fields (name, role, status)
→ API Client (admin.updateUser) → Backend Validate & Update
→ Handle Role Changes (create/update profiles)

Admin → Delete User → Confirm Action
→ API Client (admin.deleteUser) → Backend Soft Delete
→ Set is_active=false, append email suffix

Tutor Approval:
Admin → View Pending Tutors (admin.listPendingTutors)
→ Backend Query (status="pending_approval") → Return List with Stats

Admin → Review Profile → Check Documents/Experience/Subjects

Admin → Approve:
  API Client (admin.approveTutor)
  → Backend Update (approved, verified) → Notify Tutor
  → Profile Goes Live

Admin → Reject:
  API Client (admin.rejectTutor with reason)
  → Backend Update (rejected, store reason) → Notify Tutor
  → Tutor Can Revise

Activity Monitoring:
Dashboard → Auto-refresh Recent Activities (every 30s)
→ Backend Query (bookings, registrations, submissions)
→ Display Timeline

Upcoming Sessions:
Dashboard → Load Upcoming Sessions
→ Backend Query (start_time > NOW, status PENDING/CONFIRMED)
→ Display List with Details
```

**Key Files:**
- Frontend: `frontend/app/admin/page.tsx`, `frontend/components/dashboards/AdminDashboard.tsx`
- Backend: `backend/modules/admin/presentation/api.py`
- API: `frontend/lib/api.ts` (lines 1115-1233)

[📖 Full Documentation](./06_ADMIN_DASHBOARD_FLOW.md)

---

## 🔗 Cross-Flow Dependencies

### Authentication → All Flows
Every protected API endpoint requires JWT token from authentication flow.

```
API Request → Interceptor Adds Token → Backend Validates JWT
→ Load User from DB → Check is_active → Return User to Handler
```

### Booking → Messaging
After booking confirmed, messaging is unrestricted (no PII masking).

```
Create Booking → Status: CONFIRMED → has_active_booking(user1, user2) = true
→ Send Message → Service Checks Active Booking → Skip PII Masking
```

### Booking → Review
Reviews can only be created after booking completion.

```
Complete Booking → Status: COMPLETED → Student Can Review
→ Submit Review → Validate booking_id → Create Review
→ Update Tutor average_rating
```

### Student Profile → Booking
Package credits automatically deducted on booking.

```
Create Booking with package_id → Service Check Package
→ Validate remaining_credits > 0 → Create Booking
→ Deduct Credit (remaining_credits - 1)
→ If credits = 0, Mark Package "used"
```

### Tutor Onboarding → Admin Dashboard
Admin approval required before tutor profile goes live.

```
Tutor Submits → Status: "pending_approval"
→ Admin Reviews → Approve → Status: "approved", is_verified: true
→ Profile Visible in Search → Can Receive Bookings
```

---

## 📊 Data Flow Summary

### Request Journey
```
1. Frontend Component
   ↓ (User Action)
2. API Client Method (frontend/lib/api.ts)
   ↓ (HTTP Request with JWT)
3. Backend Router (backend/modules/*/presentation/api.py)
   ↓ (Validation & Auth Check)
4. Service Layer (backend/modules/*/application/services.py)
   ↓ (Business Logic)
5. Repository/Database (SQLAlchemy ORM)
   ↓ (SQL Query)
6. PostgreSQL Database
   ↓ (Result Set)
7. Service Layer (transform to DTO)
   ↓ (Response Schema)
8. Backend Router (return JSON)
   ↓ (HTTP Response)
9. API Client (normalize data)
   ↓ (State Update)
10. Frontend Component (render UI)
```

### Real-Time Updates (WebSocket)
```
1. Frontend WebSocket Connection (/ws?token=JWT)
   ↓
2. Backend WebSocket Manager (authenticate, store connection)
   ↓
3. Event Trigger (message sent, booking confirmed, etc.)
   ↓
4. Backend Broadcast (send JSON to user's connections)
   ↓
5. Frontend WebSocket Handler (receive event)
   ↓
6. Component State Update (update UI without refresh)
```

---

## 🔍 Quick File Finder

### Frontend Structure
```
frontend/
├── app/                              # Next.js pages
│   ├── (public)/login/              # Authentication
│   ├── (public)/register/
│   ├── tutors/[id]/book/            # Booking
│   ├── messages/                     # Messaging
│   ├── tutor/onboarding/            # Tutor flow
│   ├── saved-tutors/                # Student favorites
│   └── admin/                       # Admin dashboard
├── lib/api.ts                       # API client (all methods)
├── hooks/
│   ├── useWebSocket.ts              # WebSocket connection
│   └── useMessaging.ts              # Messaging logic
└── components/
    └── dashboards/
        ├── TutorDashboard.tsx
        ├── StudentDashboard.tsx
        └── AdminDashboard.tsx
```

### Backend Structure
```
backend/
├── modules/
│   ├── auth/presentation/api.py         # Auth endpoints
│   ├── bookings/presentation/api.py     # Booking endpoints
│   ├── messages/api.py                  # Messaging endpoints
│   ├── tutor_profile/presentation/api.py # Tutor endpoints
│   ├── students/presentation/api.py     # Student endpoints
│   ├── admin/presentation/api.py        # Admin endpoints
│   └── */application/services.py        # Business logic
├── core/
│   ├── dependencies.py                  # Auth dependencies
│   ├── auth.py                          # JWT utilities
│   └── message_storage.py               # File uploads
└── models.py                            # Database models
```

---

## 📝 Documentation Index

1. [Authentication Flow](./01_AUTHENTICATION_FLOW.md) - Registration, login, JWT, sessions
2. [Booking Flow](./02_BOOKING_FLOW.md) - Search, book, confirm, cancel, reschedule, review
3. [Messaging Flow](./03_MESSAGING_FLOW.md) - Send, receive, WebSocket, attachments, read receipts
4. [Tutor Onboarding Flow](./04_TUTOR_ONBOARDING_FLOW.md) - Profile, documents, approval
5. [Student Profile Flow](./05_STUDENT_PROFILE_FLOW.md) - Profile, favorites, packages
6. [Admin Dashboard Flow](./06_ADMIN_DASHBOARD_FLOW.md) - User management, analytics, approval

**Main Index:** [README.md](./README.md)

---

**Last Updated:** January 24, 2026
