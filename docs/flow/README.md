# Platform Flows Index

This directory contains comprehensive flow documentation for all major features of the tutoring platform. Each document traces the complete execution path from frontend to backend, including API calls, service layer processing, database operations, and real-time updates.

## 📋 Table of Contents

### Core Flows
1. [Authentication Flow](./01_AUTHENTICATION_FLOW.md) - User registration, login, session management
2. [Booking Flow](./02_BOOKING_FLOW.md) - Session booking, confirmation, rescheduling, cancellation
3. [Messaging Flow](./03_MESSAGING_FLOW.md) - Real-time messaging, file attachments, read receipts
4. [Tutor Onboarding Flow](./04_TUTOR_ONBOARDING_FLOW.md) - Profile creation, approval, subject setup
5. [Student Profile Flow](./05_STUDENT_PROFILE_FLOW.md) - Profile management, favorites, package purchases
6. [Admin Dashboard Flow](./06_ADMIN_DASHBOARD_FLOW.md) - User management, tutor approval, analytics

---

## 🔐 01. Authentication Flow

**Purpose:** User account creation, login, and session management

**Key Features:**
- Email/password registration with role assignment (student/tutor/admin)
- JWT-based authentication with 30-minute token expiry
- Rate limiting (5/min registration, 10/min login)
- Secure cookie storage with SameSite protection

**Critical Files:**
- Frontend: `frontend/app/(public)/login/page.tsx`, `frontend/lib/api.ts`
- Backend: `backend/modules/auth/presentation/api.py`, `backend/modules/auth/application/services.py`
- Database: `users` table

**Flow Diagram:**
```
User Form → API Client → Backend Validation → Service Layer → Database → JWT Token → Cookie Storage
```

[📖 View Full Documentation](./01_AUTHENTICATION_FLOW.md)

---

## 📅 02. Booking Flow

**Purpose:** End-to-end tutoring session management

**Key Features:**
- Tutor discovery with filtering (subject, price, rating)
- Availability-aware booking creation
- Conflict detection and validation
- Automatic/manual confirmation
- Rescheduling with 12-hour policy
- Cancellation with refund policy
- No-show management (10-minute window)
- Post-session reviews

**Critical Files:**
- Frontend: `frontend/app/tutors/[id]/book/page.tsx`, `frontend/app/bookings/page.tsx`
- Backend: `backend/modules/bookings/presentation/api.py`, `backend/modules/bookings/service.py`, `backend/modules/bookings/policy_engine.py`
- Database: `bookings`, `tutor_profile`, `reviews` tables

**Flow Diagram:**
```
Tutor Search → Profile View → Time Selection → Booking Creation → 
Tutor Confirmation → Session → Review Submission
```

**Business Rules:**
- **Cancellation Policy:** Full refund if ≥12 hours before, no refund if <12 hours
- **Rescheduling Policy:** Allowed if ≥12 hours before original time
- **No-Show Window:** Report 10+ minutes after start, within 24 hours

[📖 View Full Documentation](./02_BOOKING_FLOW.md)

---

## 💬 03. Messaging Flow

**Purpose:** Real-time communication between students and tutors

**Key Features:**
- Direct messaging with WebSocket real-time delivery
- File attachments (images, documents) with virus scanning
- Read receipts and typing indicators
- Message search (full-text)
- Thread management with unread counts
- Edit messages (within 15 minutes)
- Soft delete with audit trail
- PII masking (pre-booking contacts)

**Critical Files:**
- Frontend: `frontend/app/messages/page.tsx`, `frontend/hooks/useWebSocket.ts`
- Backend: `backend/modules/messages/api.py`, `backend/modules/messages/websocket.py`, `backend/core/message_storage.py`
- Database: `messages`, `message_attachments` tables

**Flow Diagram:**
```
Message Compose → API Send → Service Validation → Database Insert → 
WebSocket Broadcast → Real-Time Delivery → Read Receipt
```

**Security Features:**
- PII masking before active booking
- Presigned URLs for file downloads (1-hour expiry)
- Access control (sender/recipient only)
- Virus scan integration placeholder

[📖 View Full Documentation](./03_MESSAGING_FLOW.md)

---

## 👨‍🏫 04. Tutor Onboarding Flow

**Purpose:** Tutor profile creation and approval process

**Key Features:**
- Multi-step profile builder
- Subject and pricing configuration
- Certification and education uploads
- Video introduction
- Availability schedule setup
- Admin review and approval
- Profile visibility control

**Critical Files:**
- Frontend: `frontend/app/tutor/onboarding/page.tsx`, `frontend/app/tutor/profile/page.tsx`
- Backend: `backend/modules/tutor_profile/presentation/api.py`, `backend/modules/admin/presentation/api.py`
- Database: `tutor_profile`, `tutor_subjects`, `tutor_certifications`, `tutor_education`, `tutor_availability` tables

**Flow Diagram:**
```
Registration → Profile Builder → Subject Setup → Pricing Config → 
Upload Credentials → Submit Review → Admin Approval → Profile Live
```

**Approval Statuses:**
- `draft` - Incomplete profile
- `pending_approval` - Submitted for review
- `approved` - Live and visible to students
- `rejected` - Needs revision

[📖 View Full Documentation](./04_TUTOR_ONBOARDING_FLOW.md)

---

## 👨‍🎓 05. Student Profile Flow

**Purpose:** Student account management and learning tools

**Key Features:**
- Profile customization (bio, interests, goals)
- Favorite tutors management
- Learning preferences
- Package purchase and tracking
- Booking history
- Review submissions

**Critical Files:**
- Frontend: `frontend/app/profile/page.tsx`, `frontend/app/saved-tutors/page.tsx`
- Backend: `backend/modules/students/presentation/api.py`, `backend/modules/profiles/presentation/api.py`
- Database: `student_profile`, `favorite_tutors`, `student_packages` tables

**Flow Diagram:**
```
Profile Creation → Preferences Setup → Browse Tutors → Add Favorites → 
Purchase Package → Book Sessions
```

**Package Features:**
- Bulk session credits at discounted rates
- Automatic credit deduction on booking
- Expiration tracking
- Refund on cancellation (policy-based)

[📖 View Full Documentation](./05_STUDENT_PROFILE_FLOW.md)

---

## 🛠️ 06. Admin Dashboard Flow

**Purpose:** Platform management and oversight

**Key Features:**
- User management (CRUD operations)
- Tutor approval workflow
- System analytics and metrics
- Activity monitoring
- Revenue tracking
- Subject distribution analysis

**Critical Files:**
- Frontend: `frontend/app/admin/page.tsx`, `frontend/components/dashboards/AdminDashboard.tsx`
- Backend: `backend/modules/admin/presentation/api.py`
- Database: All tables (read-only analytics queries)

**Flow Diagram:**
```
Admin Login → Dashboard View → Pending Tutors → Review Profile → 
Approve/Reject → Notifications Sent
```

**Key Metrics:**
- Total users (students, tutors, admins)
- Booking statistics (pending, completed, cancelled)
- Revenue (monthly, by subject)
- User growth trends
- Session completion rates

[📖 View Full Documentation](./06_ADMIN_DASHBOARD_FLOW.md)

---

## 🔄 Cross-Flow Interactions

### Authentication + All Flows
Every protected endpoint requires JWT authentication via `get_current_user` dependency.

### Booking + Messaging
- Messages can be linked to bookings (`booking_id` field)
- Post-booking, unrestricted messaging allowed (no PII masking)

### Booking + Reviews
- Reviews created after booking completion
- Average rating calculated and cached on tutor profile

### Student Profile + Booking
- Package credits automatically deducted on booking
- Credits restored on cancellation (policy-based)

### Admin Dashboard + Tutor Onboarding
- Admin approval required before tutor profile goes live
- Rejection triggers notification with feedback

---

## 📊 Technology Stack Reference

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **State Management:** React Hooks (useState, useEffect, useContext)
- **API Client:** Axios with interceptors
- **Real-Time:** WebSocket (native)
- **Styling:** Tailwind CSS

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Architecture:** Domain-Driven Design (DDD) + Clean Architecture
- **Authentication:** JWT (jose library)
- **Database ORM:** SQLAlchemy
- **Validation:** Pydantic v2
- **Rate Limiting:** SlowAPI
- **WebSocket:** FastAPI native
- **File Storage:** S3/MinIO with presigned URLs

### Database
- **RDBMS:** PostgreSQL 17
- **Indexing:** B-tree, GIN (full-text search)
- **Constraints:** CHECK, FOREIGN KEY, UNIQUE
- **Principles:** No triggers, all logic in application code

---

## 🎯 How to Use These Documents

### For Developers
1. **Understanding Features:** Read the flow docs to understand end-to-end feature implementation
2. **Debugging:** Trace issues through the documented execution path
3. **Code Review:** Verify implementations follow the documented patterns
4. **Onboarding:** New developers can quickly understand system architecture

### For Product Managers
1. **Feature Behavior:** Understand how features work from user perspective
2. **Business Rules:** Review policies (cancellation, refunds, approval)
3. **Edge Cases:** See how system handles errors and validation

### For QA/Testing
1. **Test Case Design:** Use flows to create comprehensive test scenarios
2. **Integration Testing:** Understand dependencies between components
3. **Error Validation:** Verify error messages match documentation

---

## 🔧 Maintenance

### Updating Documentation
When modifying code that affects these flows:

1. **Update Flow Doc:** Modify the relevant `.md` file with changes
2. **Update Code References:** Ensure line numbers and file paths are current
3. **Add New Flows:** Create new flow docs for major features
4. **Review Cross-Flow Impact:** Check if changes affect multiple flows

### Document Structure
Each flow document follows this pattern:
1. **Table of Contents** - Quick navigation
2. **Step-by-Step Flow** - Frontend → API Client → Backend → Service → Database
3. **Code Snippets** - Real code from the codebase
4. **HTTP Details** - Request/response formats
5. **Business Rules** - Policies and validation
6. **Error Handling** - Common errors and responses
7. **Related Files** - All files involved in the flow

---

## 📚 Additional Resources

- **API Reference:** `docs/API_REFERENCE.md`
- **Database Architecture:** `docs/architecture/DATABASE_ARCHITECTURE.md`
- **Development Guide:** `CLAUDE.md`
- **Testing Guide:** `docs/tests/TESTING_GUIDE.md`

---

## 🤝 Contributing

When adding new features:

1. Create a new flow document following the existing pattern
2. Include all layers: Frontend → API → Backend → Database
3. Document business rules and policies
4. Add error handling scenarios
5. Link to related flows
6. Update this index file

---

**Last Updated:** January 24, 2026
**Maintained By:** Development Team
**Version:** 1.0
