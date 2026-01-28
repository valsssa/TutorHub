# COMPREHENSIVE TEST PLAN
## Tutoring Marketplace Platform

**Version:** 1.0
**Date:** 2026-01-20
**Status:** In Development

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Test Objectives](#test-objectives)
3. [Test Scope](#test-scope)
4. [Complete User Journey Maps](#complete-user-journey-maps)
5. [Test Categories](#test-categories)
6. [Detailed Test Plans](#detailed-test-plans)
7. [Test Implementation Roadmap](#test-implementation-roadmap)
8. [Test Execution Strategy](#test-execution-strategy)
9. [Success Criteria](#success-criteria)

---

## Executive Summary

This comprehensive test plan covers all user flows, API endpoints, and UI components for the tutoring marketplace platform. The platform supports three user roles (Student, Tutor, Admin) with distinct workflows for session booking, messaging, payments, and administrative management.

### Current Coverage
- **Backend API Tests:** 64% coverage (45+ of 70+ endpoints)
- **Frontend Component Tests:** 27% coverage (8 of 30+ components)
- **Integration Tests:** 20% coverage (3 of 15+ flows)
- **E2E User Flows:** 12% coverage (1 of 8+ complete journeys)

### Target Coverage
- **Backend API Tests:** 95% coverage
- **Frontend Component Tests:** 85% coverage
- **Integration Tests:** 90% coverage
- **E2E User Flows:** 100% coverage (all critical paths)

---

## Test Objectives

### Primary Objectives
1. **Validate all user flows** from registration to completion
2. **Ensure data integrity** across all transactions
3. **Verify security controls** (auth, authorization, data protection)
4. **Confirm UI/UX functionality** across all pages and components
5. **Test integration points** between frontend, backend, database, and external services
6. **Validate business logic** (pricing, refunds, scheduling, conflicts)

### Quality Gates
- All critical user flows must pass E2E tests
- API response times < 500ms for 95th percentile
- Zero security vulnerabilities in authentication/authorization
- Mobile responsiveness for all public-facing pages
- Accessibility compliance (WCAG 2.1 Level AA)

---

## Test Scope

### In Scope
✅ All user roles (Student, Tutor, Admin)
✅ All API endpoints (auth, bookings, messages, payments, profiles)
✅ All frontend pages and components
✅ Real-time messaging via WebSocket
✅ Payment processing and refunds
✅ Database transactions and integrity
✅ Security and authorization
✅ Email notifications
✅ File uploads (avatars, certifications)
✅ Multi-currency and timezone support
✅ Rate limiting and error handling

### Out of Scope
❌ Third-party service internals (Stripe, AWS S3)
❌ Browser compatibility testing (assume modern browsers)
❌ Performance load testing (separate effort)
❌ Internationalization (i18n) beyond currency/timezone

---

## Complete User Journey Maps

### Journey 1: Student Registration to First Review

```
┌─────────────────────────────────────────────────────────────────────┐
│ STUDENT JOURNEY: Registration → Search → Book → Attend → Review   │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Registration
  → Navigate to /register
  → Fill form: email, password, confirm password
  → Select role: "Student"
  → Click "Sign Up"
  → Backend: POST /api/auth/register
  → Creates User (role=student), StudentProfile
  → Auto-detects timezone, currency
  → Redirect to /login

Step 2: Login
  → Navigate to /login
  → Enter email, password
  → Backend: POST /api/auth/login
  → Returns JWT token
  → Store in cookie
  → Redirect to /dashboard

Step 3: View Dashboard
  → Load StudentDashboard component
  → Backend: GET /users/me
  → Display: Upcoming sessions, Recommendations, CTA

Step 4: Search for Tutor
  → Navigate to /tutors
  → Backend: GET /api/tutors?subject_id=1&sort_by=rating
  → Apply filters: Subject, Price range, Rating
  → View tutor cards with ratings, hourly rate

Step 5: View Tutor Profile
  → Click tutor card
  → Navigate to /tutors/[id]
  → Backend: GET /api/tutors/{id}
  → Display: Bio, Reviews, Subjects, Availability, Pricing
  → Backend: GET /api/tutors/{id}/reviews

Step 6: Book Session
  → Click "Book Session" button
  → Opens ModernBookingModal
  → Select: Subject, Date, Time, Duration
  → Add notes (optional)
  → Backend: GET /api/tutors/{id}/availability
  → Validate: No conflicts
  → Submit booking
  → Backend: POST /api/bookings
  → Creates Booking (status=PENDING if !auto_confirm, else CONFIRMED)
  → Notification sent to tutor
  → Redirect to /bookings

Step 7: View Bookings
  → Load BookingsPageContent
  → Backend: GET /api/bookings?role=student
  → Display: Pending, Upcoming, Completed tabs
  → Status badge, Join button (if within 15 min)

Step 8: Wait for Tutor Confirmation
  → Tutor receives notification
  → Tutor approves booking
  → Backend: POST /api/tutor/bookings/{id}/confirm
  → Booking status → CONFIRMED
  → Student receives notification

Step 9: Pre-Session Messaging
  → Navigate to /messages
  → Backend: GET /api/messages/threads
  → Click tutor thread
  → Backend: GET /api/messages/threads/{tutor_id}
  → WebSocket connection established
  → Send message: "Looking forward to our session!"
  → Backend: POST /api/messages
  → Tutor receives real-time message

Step 10: Join Session
  → At scheduled time (within 15 min window)
  → Click "Join" button on booking card
  → Opens video meeting (join_url)
  → Session occurs (external to platform)

Step 11: Session Completion
  → After end_time passes
  → Backend: Cron job marks booking as COMPLETED
  → Student receives notification to review

Step 12: Submit Review
  → Navigate to /bookings
  → Click "Review" button on completed booking
  → Navigate to /bookings/[id]/review
  → Backend: GET /api/bookings/{id}
  → Fill: 5-star rating, comment
  → Submit
  → Backend: POST /api/reviews
  → Creates Review (with booking_snapshot)
  → Updates tutor average_rating
  → Redirect to /bookings
  → Success message displayed

✅ End of Student Journey
```

**Test Coverage Required:**
- [ ] Frontend E2E test (Playwright/Cypress)
- [ ] Backend integration test (all endpoints)
- [ ] Database state validation at each step
- [ ] Notification delivery verification
- [ ] WebSocket message flow
- [ ] Payment transaction (if applicable)

---

### Journey 2: Tutor Onboarding to First Booking

```
┌─────────────────────────────────────────────────────────────────────┐
│ TUTOR JOURNEY: Registration → Onboarding → Approval → Accept       │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Registration
  → Navigate to /register
  → Fill form: email, password
  → Select role: "Tutor"
  → Click "Sign Up"
  → Backend: POST /api/auth/register (role=tutor)
  → Creates User, TutorProfile (status=incomplete)
  → Auto-login after registration
  → Redirect to /tutor/onboarding

Step 2: Tutor Onboarding (8-step wizard)

  Step 2a: Personal Information
    → Fill: First name, Last name, Country, Phone
    → Select: Primary subject, Timezone
    → Write: Brief introduction
    → Click "Next"

  Step 2b: Education
    → Add education entries:
      - Degree, School, Field of study
      - Start year, End year
      - Upload certificate (optional)
    → Click "Next"

  Step 2c: Certifications
    → Add certifications:
      - Name, Issuing org, Issue date, Expiry
      - Upload document
    → Backend: POST /api/users/avatar/signed-url (for cert files)
    → Upload to S3
    → Click "Next"

  Step 2d: Availability
    → Set weekly schedule:
      - Mon-Sun: Start time, End time
      - Hours per week calculation
    → Set timezone
    → Click "Next"

  Step 2e: Teaching Details
    → Fill: Years of experience, Teaching bio
    → Select: Subject expertise (multiple)
    → Set: Proficiency levels (CEFR)
    → Click "Next"

  Step 2f: Languages
    → Add languages: Language code, Proficiency
    → Click "Next"

  Step 2g: Pricing
    → Set: Hourly rate (USD)
    → Add pricing packages (optional):
      - "5 sessions for $250"
      - Session count, Price, Description
    → Click "Next"

  Step 2h: Review & Submit
    → Review all entered data
    → Agree to terms
    → Click "Submit for Approval"
    → Backend: PUT /api/tutors/me/profile
    → Updates TutorProfile (status=pending_approval)
    → Redirect to /tutor/profile/submitted
    → Display: "Profile under review" message

Step 3: Admin Approval
  → Admin navigates to /admin
  → Click "User Management" tab
  → View "Pending Tutors" section
  → Backend: GET /api/admin/tutors/pending
  → Click tutor profile to review
  → Verify: Certifications, education, bio
  → Decision:
    - Approve: POST /api/admin/tutors/{id}/approve
      → TutorProfile.status → approved
      → TutorProfile.is_approved → true
      → Notification sent to tutor
    - Reject: POST /api/admin/tutors/{id}/reject
      → TutorProfile.status → rejected
      → Rejection reason stored
      → Notification sent to tutor

Step 4: Tutor Dashboard Access (After Approval)
  → Tutor logs in
  → Navigate to /dashboard
  → Loads TutorDashboard component
  → Backend: GET /users/me
  → Backend: GET /api/tutor/bookings?status=pending
  → Display:
    - Earnings summary
    - Pending booking requests
    - Upcoming confirmed sessions
    - Availability calendar

Step 5: Receive Booking Request
  → Student creates booking (see Student Journey Step 6)
  → Tutor receives notification
  → Backend: Create Notification (type=booking_request)
  → Dashboard shows pending request

Step 6: Review Booking Request
  → View booking details:
    - Student name, Subject, Date/Time
    - Duration, Notes from student
    - Proposed price
  → Check for conflicts
  → Backend: GET /api/bookings/{id}

Step 7: Approve Booking
  → Click "Approve" button
  → Backend: POST /api/tutor/bookings/{id}/confirm
  → Booking status → CONFIRMED
  → Creates Payment (if payment required)
  → Student notified
  → Adds to tutor's schedule

Step 8: Pre-Session Messaging
  → Navigate to /messages
  → Click student thread
  → Send message: "See you on [date]!"
  → WebSocket delivers to student in real-time

Step 9: Join Session
  → At scheduled time
  → Click "Join" on booking card
  → Opens video meeting

Step 10: Post-Session
  → After end_time
  → Booking status → COMPLETED
  → Earnings added to tutor balance
  → Backend: Update TutorProfile.total_sessions += 1
  → Student prompted to review
  → Tutor can view session in history

✅ End of Tutor Journey
```

**Test Coverage Required:**
- [ ] Frontend E2E test (onboarding wizard)
- [ ] Backend tutor profile CRUD tests
- [ ] File upload integration test (certifications)
- [ ] Admin approval workflow test
- [ ] Booking acceptance integration test
- [ ] Earnings calculation verification

---

### Journey 3: Admin User Management

```
┌─────────────────────────────────────────────────────────────────────┐
│ ADMIN JOURNEY: Login → Manage Users → Approve Tutors → Analytics   │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Admin Login
  → Navigate to /login
  → Enter admin credentials
  → Backend: POST /api/auth/login
  → Returns JWT with role=admin
  → Redirect to /admin

Step 2: Admin Dashboard
  → Loads AdminDashboard component
  → Backend: GET /api/admin/dashboard/stats
  → Display metrics:
    - Total users, Active tutors, Sessions today, Revenue
  → Backend: GET /api/admin/dashboard/recent-activities
  → Display recent signups, bookings

Step 3: User Management
  → Click "User Management" tab
  → Backend: GET /api/admin/users?page=1&limit=50
  → Display user table:
    - Email, Role, Status, Created date
    - Search bar, Role filter, Status filter

  Action 3a: Update User Role
    → Click user row
    → Open edit modal
    → Change role: student → tutor
    → Backend: PUT /api/admin/users/{id}
    → Auto-creates TutorProfile if missing
    → Audit log created

  Action 3b: Deactivate User
    → Click "Deactivate" button
    → Confirm dialog
    → Backend: PATCH /api/admin/users/{id}
    → Sets is_active=false
    → User cannot login
    → Audit log created

  Action 3c: Delete User (Soft Delete)
    → Click "Delete" button
    → Confirm dialog with reason
    → Backend: DELETE /api/admin/users/{id}
    → Sets deleted_at timestamp
    → Preserves data for audit
    → Audit log created

Step 4: Tutor Approval Workflow
  → Click "Pending Tutors" section
  → Backend: GET /api/admin/tutors/pending
  → Display list of tutors awaiting approval
  → Click tutor to view full profile:
    - Bio, Education, Certifications
    - Subjects, Languages, Pricing
    - Uploaded documents

  Action 4a: Approve Tutor
    → Review profile completeness
    → Verify credentials (manual check)
    → Click "Approve"
    → Backend: POST /api/admin/tutors/{id}/approve
    → TutorProfile.status → approved
    → Email notification to tutor
    → Audit log: "tutor_approved"

  Action 4b: Reject Tutor
    → Identify issues (e.g., incomplete certs)
    → Enter rejection reason
    → Click "Reject"
    → Backend: POST /api/admin/tutors/{id}/reject
    → TutorProfile.status → rejected
    → Email with reason sent to tutor
    → Audit log: "tutor_rejected"

Step 5: Session Monitoring
  → Click "Sessions" tab
  → Backend: GET /api/admin/dashboard/upcoming-sessions
  → Display upcoming sessions (next 30):
    - Student, Tutor, Subject, Time, Status
  → Filter by: Date range, Status, Subject
  → Backend: GET /api/admin/dashboard/session-metrics
  → Display: Completion rate, Avg duration

Step 6: Analytics & Reporting
  → Click "Analytics" tab
  → Backend: GET /api/admin/dashboard/monthly-revenue?months=6
  → Chart: Revenue trends (line chart)
  → Backend: GET /api/admin/dashboard/subject-distribution
  → Chart: Popular subjects (pie chart)
  → Backend: GET /api/admin/dashboard/user-growth?months=12
  → Chart: User signups over time

Step 7: Audit Log Review
  → Navigate to Audit section
  → Backend: GET /api/admin/audit/logs?page=1&limit=50
  → Display audit entries:
    - Action, User, Target, Timestamp, IP address
  → Filter by: Date range, Action type, User
  → Export to CSV (optional)

Step 8: Platform Settings
  → Click "Settings" tab
  → Tabs: General, Notifications, Billing, Security

  General Settings:
    - Platform name, Logo, Default currency
    - Commission rate (default 20%)

  Billing Settings:
    - Payment gateway config (Stripe keys)
    - Refund policy parameters

  Security Settings:
    - Rate limiting thresholds
    - Session timeout duration
    - 2FA enforcement

✅ End of Admin Journey
```

**Test Coverage Required:**
- [ ] Frontend E2E admin workflow test
- [ ] Admin API endpoint tests (all actions)
- [ ] Role-based access control verification
- [ ] Audit log integrity tests
- [ ] Analytics data accuracy tests

---

### Journey 4: Payment and Refund Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ PAYMENT JOURNEY: Booking → Payment → Session → Refund (if needed)  │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Booking Initiated
  → Student creates booking
  → Backend: POST /api/bookings
  → Calculates total:
    - Hourly rate × Duration
    - Platform fee (20%)
    - Currency conversion (if needed)

Step 2: Payment Intent Created
  → Backend: Create PaymentIntent via Stripe API
  → Store: payment_intent_id on Booking
  → Frontend: Receives client_secret
  → Display: Payment form (Stripe Elements)

Step 3: Payment Submission
  → Student enters card details
  → Stripe validates card
  → Frontend: confirmPayment(client_secret)
  → Stripe processes payment
  → Webhook: payment_intent.succeeded
  → Backend: POST /api/webhooks/stripe
  → Updates Booking.payment_status → paid
  → Creates Payment record
  → Tutor notified of new booking

Step 4: Session Completion
  → Session occurs
  → Booking status → COMPLETED
  → Backend: Calculate earnings:
    - Tutor earnings = total_amount - platform_fee
    - Platform fee = 20% of total_amount
  → Update: TutorProfile.total_earnings += tutor_earnings

Step 5: Refund Scenario 1 - Student Cancels >12h Before
  → Student clicks "Cancel" on booking
  → Backend: POST /api/bookings/{id}/cancel
  → Check: Time until start_time > 12 hours
  → Refund policy: 100% refund
  → Backend: Create Refund via Stripe API
  → Update: Booking.status → CANCELLED_BY_STUDENT
  → Update: Booking.refund_amount = total_amount
  → Create: Payment record (type=refund)
  → Notifications sent to both parties
  → Audit log created

Step 6: Refund Scenario 2 - Student Cancels <12h Before
  → Student attempts to cancel
  → Backend: POST /api/bookings/{id}/cancel
  → Check: Time until start_time < 12 hours
  → Refund policy: 0% refund
  → Warning shown to student
  → Confirm cancellation anyway
  → Booking status → CANCELLED_BY_STUDENT
  → No refund issued
  → Tutor compensated for lost time slot

Step 7: Refund Scenario 3 - Tutor Declines
  → Tutor clicks "Decline" on pending booking
  → Backend: POST /api/tutor/bookings/{id}/decline
  → Refund policy: 100% automatic refund
  → Backend: Create Refund via Stripe API
  → Booking status → CANCELLED_BY_TUTOR
  → Refund amount = 100%
  → Student notified with refund details

Step 8: Refund Scenario 4 - No-Show
  → Tutor marks student no-show (>10 min after start)
  → Backend: POST /api/tutor/bookings/{id}/mark-no-show-student
  → Verify: current_time > start_time + 10 minutes
  → Verify: current_time < start_time + 24 hours
  → Booking status → NO_SHOW_STUDENT
  → Refund policy: 0% refund (tutor compensated)
  → No refund issued
  → Dispute process available to student

✅ End of Payment Journey
```

**Test Coverage Required:**
- [ ] Backend payment integration tests (Stripe mocks)
- [ ] Refund policy logic tests (all scenarios)
- [ ] Webhook processing tests
- [ ] Currency conversion tests
- [ ] Payment failure handling tests
- [ ] Dispute resolution tests

---

### Journey 5: Real-Time Messaging Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ MESSAGING JOURNEY: Connect → Send → Receive → Read Receipts        │
└─────────────────────────────────────────────────────────────────────┘

Step 1: WebSocket Connection
  → User navigates to /messages
  → Frontend: const ws = new WebSocket(`wss://api.../ws?token=${jwt}`)
  → Backend: Authenticate token
  → Backend: WebSocketManager.connect(ws, user_id)
  → Connection stored in active_connections
  → Connection status: "Connected" (green indicator)

Step 2: Load Message Threads
  → Backend: GET /api/messages/threads
  → Returns list of conversations:
    - other_user_id, name, avatar
    - last_message, unread_count
    - last_activity timestamp
  → Frontend: Display thread list (sorted by recency)

Step 3: Open Conversation
  → User clicks thread
  → Backend: GET /api/messages/threads/{other_user_id}?limit=50&offset=0
  → Returns messages (paginated)
  → Frontend: Display MessageBubble components
  → Auto-scroll to bottom
  → Mark messages as read:
    → Backend: PATCH /api/messages/threads/{other_user_id}/read-all

Step 4: Send Message
  → User types message in MessageInput
  → Click "Send" or press Enter
  → Frontend: POST /api/messages
  → Request body: { recipient_id, message, booking_id? }
  → Backend: Validate participants
  → Backend: Sanitize message (PII masking if pre-booking)
  → Backend: Create Message record
  → Backend: WebSocket broadcast to recipient
  → WebSocket event: { type: "new_message", message: {...} }
  → Recipient's UI updates in real-time

Step 5: Receive Message (Real-Time)
  → Recipient's WebSocket receives event
  → Frontend: useWebSocket hook processes event
  → Update: message list state
  → Display: New message bubble
  → Play: Notification sound (if enabled)
  → Show: Unread badge on thread list
  → Auto-scroll to new message

Step 6: Typing Indicator
  → Sender types in input field
  → Frontend: Debounced typing event
  → WebSocket: Send { type: "typing", recipient_id }
  → Backend: Broadcast to recipient
  → Recipient sees: "User is typing..." indicator
  → Timeout: 3 seconds of inactivity clears indicator

Step 7: Read Receipt
  → Recipient views message thread
  → Backend: PATCH /api/messages/{message_id}/read
  → Update: Message.is_read = true, read_at = now()
  → WebSocket: Send { type: "message_read", message_id, read_at }
  → Sender's UI updates: Checkmark turns blue (read)

Step 8: Edit Message
  → Sender clicks "Edit" on own message
  → Frontend: Enable edit mode in MessageBubble
  → User edits text, clicks "Save"
  → Validation: Within 15-minute window
  → Backend: PATCH /api/messages/{message_id}
  → Update: Message.message = new_content, is_edited = true
  → WebSocket: Broadcast edit event
  → Both UIs show "(edited)" label

Step 9: Delete Message
  → Sender clicks "Delete" on own message
  → Confirm dialog
  → Backend: DELETE /api/messages/{message_id}
  → Soft delete: Sets deleted_at timestamp
  → WebSocket: Broadcast { type: "message_deleted", message_id }
  → Both UIs: Replace message with "Message deleted"

Step 10: Send Attachment
  → User clicks attachment icon
  → Select file (image, PDF, etc.)
  → Validation: File size < 10MB, allowed types
  → Backend: POST /api/users/avatar/signed-url
  → Upload to S3 with presigned URL
  → Backend: POST /api/messages/with-attachment
  → Create: MessageAttachment record
  → WebSocket: Broadcast message with attachment
  → Recipient sees: File thumbnail or download link

Step 11: Disconnect & Reconnect
  → User closes browser tab
  → WebSocket disconnects
  → Backend: WebSocketManager.disconnect(ws, user_id)
  → User reopens /messages
  → WebSocket reconnects
  → Backend: Sync unread messages
  → Display: Unread count badge

✅ End of Messaging Journey
```

**Test Coverage Required:**
- [ ] WebSocket connection/disconnection tests
- [ ] Message send/receive integration test
- [ ] Real-time broadcast verification
- [ ] Read receipt functionality test
- [ ] Typing indicator test
- [ ] Message edit/delete tests
- [ ] File attachment upload test
- [ ] Multi-device message sync test

---

### Journey 6: Tutor Availability Management

```
┌─────────────────────────────────────────────────────────────────────┐
│ AVAILABILITY JOURNEY: Set Schedule → Block Time → Handle Conflicts │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Access Availability Manager
  → Tutor navigates to /tutor/schedule
  → Backend: GET /api/tutors/me/availability
  → Returns:
    - TutorAvailability records (recurring)
    - TutorBlackout records (one-time blocks)
  → Frontend: Display calendar view with time slots

Step 2: Set Recurring Availability
  → Tutor selects day: Monday
  → Clicks "Add Time Slot"
  → TimeSlotPicker: Start time 09:00, End time 17:00
  → Click "Save"
  → Backend: POST /api/tutors/me/availability
  → Creates: TutorAvailability (day_of_week=1, start_time, end_time)
  → Validation: No overlaps with existing slots
  → Calendar updates: Monday 9am-5pm marked available

Step 3: Add Multiple Days
  → Repeat for Tuesday, Wednesday, Thursday, Friday
  → Each day gets multiple time slots if needed
  → Backend validates no conflicts within same day

Step 4: Set Blackout Period (Vacation)
  → Tutor clicks "Block Time"
  → Select date range: Dec 20-27, 2025
  → Reason: "Holiday vacation"
  → Backend: POST /api/tutors/me/blackouts
  → Creates: TutorBlackout (start_time, end_time, reason)
  → All booking requests during this period are rejected

Step 5: Booking Conflict Check
  → Student attempts to book: Monday Dec 23, 10am-11am
  → Backend: GET /api/tutors/{id}/availability?date=2025-12-23
  → Check:
    1. Is time within TutorAvailability range? → Yes (Mon 9am-5pm)
    2. Is time blocked by TutorBlackout? → Yes (Dec 20-27)
    3. Are there conflicting bookings? → N/A (blackout takes priority)
  → Result: Time slot unavailable
  → Frontend: Gray out time slot in calendar

Step 6: Buffer Time Enforcement
  → Student books: Monday Jan 6, 10am-11am
  → Another student tries: Monday Jan 6, 11am-12pm
  → Backend conflict check:
    - First booking: 10:00-11:00
    - Second booking: 11:00-12:00
    - Buffer time: 5 minutes
    - Conflict window: 9:55-11:05 vs 10:55-12:05
  → Overlap detected: 10:55-11:05
  → Result: Conflict error
  → Error message: "Tutor unavailable (buffer time)"

Step 7: Update Existing Availability
  → Tutor changes Monday hours: 10am-4pm
  → Backend: PUT /api/tutors/me/availability/{id}
  → Validation: Check for affected bookings
  → If bookings exist outside new range:
    - Warning shown to tutor
    - Must reschedule or cancel affected bookings
  → Update saved if no conflicts

Step 8: Delete Availability Slot
  → Tutor removes Friday availability
  → Backend: DELETE /api/tutors/me/availability/{id}
  → Check: Any confirmed bookings on Fridays?
  → If yes: Error - "Cannot delete, bookings exist"
  → If no: Slot deleted
  → Future students cannot book Fridays

Step 9: Timezone Handling
  → Tutor timezone: America/New_York (UTC-5)
  → Student timezone: Europe/London (UTC+0)
  → Tutor sets availability: Mon 9am-5pm EST
  → Student views: Mon 2pm-10pm GMT
  → Booking created: Stored as UTC timestamp
  → Both see session in their local times
  → Backend: Converts all times to UTC for storage

✅ End of Availability Journey
```

**Test Coverage Required:**
- [ ] Availability CRUD API tests
- [ ] Blackout period enforcement test
- [ ] Booking conflict detection test
- [ ] Buffer time validation test
- [ ] Timezone conversion accuracy test
- [ ] Calendar UI integration test

---

## Test Categories

### 1. Unit Tests

**Backend Unit Tests (Python/pytest)**
- Models (database entities)
- Services (business logic)
- Utilities (helpers, validators)
- Security (password hashing, JWT)

**Frontend Unit Tests (TypeScript/Jest)**
- Components (rendering, props, events)
- Hooks (state management, API calls)
- Utilities (formatters, validators)
- Context providers

### 2. Integration Tests

**Backend API Integration (pytest + TestClient)**
- Endpoint request/response validation
- Database transaction verification
- Authentication/authorization flows
- Cross-module interactions

**Frontend Integration (Jest + React Testing Library)**
- Component interactions
- Form submissions
- API client integration
- Router navigation

### 3. End-to-End (E2E) Tests

**User Flow Tests (Playwright/Cypress)**
- Complete user journeys
- Multi-page workflows
- Real-time features (WebSocket)
- Payment processing (Stripe test mode)

### 4. API Contract Tests

**OpenAPI Schema Validation**
- Request schema compliance
- Response schema compliance
- Error response formats
- API versioning

### 5. Security Tests

**Authentication & Authorization**
- JWT validation
- Role-based access control
- Session management
- Rate limiting

**Input Validation**
- SQL injection prevention
- XSS prevention
- CSRF protection
- File upload validation

### 6. Performance Tests

**Load Testing (Locust/k6)**
- Concurrent user sessions
- API response times
- Database query performance
- WebSocket scalability

---

## Detailed Test Plans

### Backend Unit Tests (Detailed)

#### 1. Tutor Profile Service Tests
**File:** `backend/modules/tutor_profile/tests/test_services.py`

```python
class TestTutorProfileService:
    def test_create_profile_success(db, test_tutor_user):
        """Test successful tutor profile creation"""
        # Given
        profile_data = {
            "title": "Math Expert",
            "bio": "10 years experience",
            "hourly_rate": 50.00,
            "experience_years": 10
        }

        # When
        profile = TutorProfileService.create_profile(db, test_tutor_user.id, profile_data)

        # Then
        assert profile.user_id == test_tutor_user.id
        assert profile.title == "Math Expert"
        assert profile.hourly_rate == Decimal("50.00")
        assert profile.profile_status == "incomplete"

    def test_create_profile_duplicate_error(db, test_tutor_with_profile):
        """Test error when creating duplicate profile"""
        # When/Then
        with pytest.raises(ValueError, match="Profile already exists"):
            TutorProfileService.create_profile(db, test_tutor_with_profile.id, {})

    def test_update_profile_subjects(db, test_tutor_profile):
        """Test updating tutor subjects"""
        # Given
        subjects = [
            {"subject_id": 1, "proficiency_level": "C2", "years_experience": 5},
            {"subject_id": 2, "proficiency_level": "B2", "years_experience": 3}
        ]

        # When
        updated = TutorProfileService.update_subjects(db, test_tutor_profile.id, subjects)

        # Then
        assert len(updated.subjects) == 2
        assert updated.subjects[0].proficiency_level == "C2"

    def test_calculate_completion_percentage(db, test_tutor_profile):
        """Test profile completion calculation"""
        # Given - minimal profile
        assert test_tutor_profile.completion_percentage < 50

        # When - add more fields
        test_tutor_profile.title = "Expert"
        test_tutor_profile.bio = "Bio"
        test_tutor_profile.hourly_rate = 50.00
        test_tutor_profile.video_url = "https://youtube.com/..."
        db.commit()

        # Then
        completion = TutorProfileService.calculate_completion(db, test_tutor_profile.id)
        assert completion > 50

    def test_submit_for_approval(db, test_tutor_profile):
        """Test profile submission for admin review"""
        # Given - complete all required fields
        test_tutor_profile.title = "Expert"
        test_tutor_profile.bio = "Bio"
        test_tutor_profile.hourly_rate = 50.00
        test_tutor_profile.experience_years = 5
        # Add at least one subject
        db.add(TutorSubject(tutor_profile_id=test_tutor_profile.id, subject_id=1))
        db.commit()

        # When
        result = TutorProfileService.submit_for_approval(db, test_tutor_profile.id)

        # Then
        assert result.profile_status == "pending_approval"
        # Notification should be sent to admin

    def test_approve_profile(db, test_admin_user, test_tutor_profile_pending):
        """Test admin approving tutor profile"""
        # When
        approved = TutorProfileService.approve_profile(
            db,
            test_tutor_profile_pending.id,
            test_admin_user.id
        )

        # Then
        assert approved.is_approved == True
        assert approved.profile_status == "approved"
        assert approved.approved_by == test_admin_user.id
        assert approved.approved_at is not None
        # Audit log created
        # Notification sent to tutor

    def test_reject_profile(db, test_admin_user, test_tutor_profile_pending):
        """Test admin rejecting tutor profile"""
        # Given
        reason = "Certifications not verified"

        # When
        rejected = TutorProfileService.reject_profile(
            db,
            test_tutor_profile_pending.id,
            test_admin_user.id,
            reason
        )

        # Then
        assert rejected.profile_status == "rejected"
        assert rejected.rejection_reason == reason
        # Notification sent to tutor with reason
```

#### 2. Availability Service Tests
**File:** `backend/modules/tutor_profile/tests/test_availability_service.py`

```python
class TestAvailabilityService:
    def test_create_recurring_availability(db, test_tutor_profile):
        """Test creating recurring weekly availability"""
        # Given
        slots = [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},  # Monday
            {"day_of_week": 3, "start_time": "10:00", "end_time": "16:00"}   # Wednesday
        ]

        # When
        result = AvailabilityService.set_availability(db, test_tutor_profile.id, slots)

        # Then
        assert len(result) == 2
        assert result[0].day_of_week == 1

    def test_availability_overlap_same_day(db, test_tutor_profile):
        """Test error on overlapping slots same day"""
        # Given - existing slot Mon 9am-5pm
        db.add(TutorAvailability(
            tutor_profile_id=test_tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        ))
        db.commit()

        # When - try to add Mon 3pm-7pm (overlap)
        with pytest.raises(ValueError, match="Overlapping availability"):
            AvailabilityService.add_slot(db, test_tutor_profile.id, {
                "day_of_week": 1,
                "start_time": "15:00",
                "end_time": "19:00"
            })

    def test_create_blackout_period(db, test_tutor_profile):
        """Test creating vacation/blackout period"""
        # Given
        blackout = {
            "start_time": "2025-12-20T00:00:00Z",
            "end_time": "2025-12-27T23:59:59Z",
            "reason": "Holiday vacation"
        }

        # When
        result = AvailabilityService.create_blackout(db, test_tutor_profile.id, blackout)

        # Then
        assert result.reason == "Holiday vacation"
        # Future bookings during this period should be blocked

    def test_get_available_slots(db, test_tutor_profile_with_availability):
        """Test retrieving available time slots for a date"""
        # Given - Mon 9am-5pm availability
        date = datetime(2025, 1, 6, tzinfo=timezone.utc)  # Monday

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile_with_availability.id,
            date,
            duration_minutes=60
        )

        # Then
        assert len(slots) > 0
        assert slots[0]["start_time"].hour == 9

    def test_available_slots_exclude_bookings(db, test_tutor_profile, test_booking):
        """Test that booked slots are excluded from available slots"""
        # Given - Mon 9am-5pm availability + booking 10am-11am
        date = test_booking.start_time.date()

        # When
        slots = AvailabilityService.get_available_slots(db, test_tutor_profile.id, date)

        # Then
        # 10am-11am slot should not be in available slots
        booked_time = test_booking.start_time.time()
        for slot in slots:
            assert slot["start_time"].time() != booked_time

    def test_available_slots_exclude_blackouts(db, test_tutor_profile, test_blackout):
        """Test that blackout periods exclude all slots"""
        # Given - Blackout Dec 20-27
        date = datetime(2025, 12, 23, tzinfo=timezone.utc)

        # When
        slots = AvailabilityService.get_available_slots(db, test_tutor_profile.id, date)

        # Then
        assert len(slots) == 0
```

#### 3. Payment Service Tests
**File:** `backend/modules/payments/tests/test_payment_service.py`

```python
class TestPaymentService:
    @pytest.fixture
    def mock_stripe(self, mocker):
        """Mock Stripe API"""
        return mocker.patch('stripe.PaymentIntent')

    def test_create_payment_intent(db, test_booking, mock_stripe):
        """Test Stripe payment intent creation"""
        # Given
        mock_stripe.create.return_value = MagicMock(
            id="pi_123456",
            client_secret="pi_123456_secret_abc",
            status="requires_payment_method"
        )

        # When
        intent = PaymentService.create_payment_intent(db, test_booking.id)

        # Then
        assert intent["id"] == "pi_123456"
        assert intent["client_secret"] == "pi_123456_secret_abc"
        # Booking updated with payment_intent_id
        db.refresh(test_booking)
        assert test_booking.payment_intent_id == "pi_123456"

    def test_calculate_platform_fee(self):
        """Test platform fee calculation (20%)"""
        # Given
        total_amount = Decimal("100.00")

        # When
        fee = PaymentService.calculate_platform_fee(total_amount)

        # Then
        assert fee == Decimal("20.00")
        assert total_amount - fee == Decimal("80.00")  # Tutor earnings

    def test_process_refund_full(db, test_booking_paid, mock_stripe):
        """Test full refund processing"""
        # Given
        test_booking_paid.payment_intent_id = "pi_123456"
        test_booking_paid.total_amount = Decimal("100.00")
        mock_stripe.create_refund.return_value = MagicMock(
            id="re_123456",
            status="succeeded",
            amount=10000  # cents
        )

        # When
        refund = PaymentService.process_refund(
            db,
            test_booking_paid.id,
            refund_percentage=100,
            reason="Student cancelled >12h before"
        )

        # Then
        assert refund.amount == Decimal("100.00")
        assert refund.status == "succeeded"
        db.refresh(test_booking_paid)
        assert test_booking_paid.refund_amount == Decimal("100.00")

    def test_process_refund_partial(db, test_booking_paid, mock_stripe):
        """Test partial refund (50%)"""
        # When
        refund = PaymentService.process_refund(
            db,
            test_booking_paid.id,
            refund_percentage=50,
            reason="Tutor cancelled"
        )

        # Then
        assert refund.amount == Decimal("50.00")

    def test_process_refund_policy_12h_rule(db, test_student, test_tutor_profile):
        """Test refund policy: <12h = no refund, >12h = full refund"""
        # Scenario 1: Booking in 24h (>12h) - full refund
        booking_24h = create_booking(
            db,
            student=test_student,
            tutor=test_tutor_profile,
            start_time=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        refund_amt = PaymentService.calculate_refund_amount(booking_24h)
        assert refund_amt == booking_24h.total_amount

        # Scenario 2: Booking in 6h (<12h) - no refund
        booking_6h = create_booking(
            db,
            student=test_student,
            tutor=test_tutor_profile,
            start_time=datetime.now(timezone.utc) + timedelta(hours=6)
        )
        refund_amt = PaymentService.calculate_refund_amount(booking_6h)
        assert refund_amt == Decimal("0.00")

    def test_handle_webhook_payment_succeeded(db, test_booking):
        """Test Stripe webhook: payment_intent.succeeded"""
        # Given
        webhook_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": test_booking.payment_intent_id,
                    "amount": 10000,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }

        # When
        PaymentService.handle_webhook(db, webhook_event)

        # Then
        db.refresh(test_booking)
        assert test_booking.payment_status == "paid"
        # Notification sent to tutor

    def test_handle_webhook_payment_failed(db, test_booking):
        """Test Stripe webhook: payment_intent.payment_failed"""
        # Given
        webhook_event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": test_booking.payment_intent_id,
                    "last_payment_error": {
                        "message": "Your card was declined"
                    }
                }
            }
        }

        # When
        PaymentService.handle_webhook(db, webhook_event)

        # Then
        db.refresh(test_booking)
        assert test_booking.payment_status == "failed"
        # Notification sent to student with error
```

#### 4. Package Purchase Service Tests
**File:** `backend/modules/packages/tests/test_package_service.py`

```python
class TestPackageService:
    def test_purchase_package(db, test_student, test_tutor_profile, test_pricing_option):
        """Test student purchasing a session package"""
        # Given
        pricing_option = test_pricing_option  # 5 sessions for $250

        # When
        package = PackageService.purchase_package(
            db,
            student_id=test_student.id,
            pricing_option_id=pricing_option.id
        )

        # Then
        assert package.sessions_purchased == 5
        assert package.sessions_remaining == 5
        assert package.purchase_price == Decimal("250.00")
        assert package.status == "active"

    def test_use_package_credit(db, test_student_package, test_booking):
        """Test consuming a session credit from package"""
        # Given
        initial_remaining = test_student_package.sessions_remaining

        # When
        updated = PackageService.use_credit(
            db,
            package_id=test_student_package.id,
            booking_id=test_booking.id
        )

        # Then
        assert updated.sessions_remaining == initial_remaining - 1
        assert updated.sessions_used == 1
        # Booking linked to package
        db.refresh(test_booking)
        assert test_booking.package_id == test_student_package.id

    def test_use_credit_insufficient_sessions(db, test_student_package_depleted):
        """Test error when package has no remaining sessions"""
        # Given - package with 0 remaining sessions
        assert test_student_package_depleted.sessions_remaining == 0

        # When/Then
        with pytest.raises(ValueError, match="No sessions remaining"):
            PackageService.use_credit(db, test_student_package_depleted.id, 999)

    def test_package_expiration(db, test_student_package):
        """Test package expiration after 12 months"""
        # Given
        test_student_package.purchased_at = datetime.now(timezone.utc) - timedelta(days=366)
        test_student_package.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

        # When
        PackageService.check_expirations(db)

        # Then
        db.refresh(test_student_package)
        assert test_student_package.status == "expired"

    def test_list_student_packages(db, test_student, test_student_package):
        """Test retrieving student's purchased packages"""
        # When
        packages = PackageService.list_student_packages(db, test_student.id)

        # Then
        assert len(packages) > 0
        assert packages[0].id == test_student_package.id
```

---

### Frontend Component Tests (Detailed)

#### 1. Dashboard Component Tests

**File:** `frontend/__tests__/components/dashboards/StudentDashboard.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { StudentDashboard } from '@/components/dashboards/StudentDashboard'
import { mockUser, mockBookings } from '@/test-utils/mocks'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() })
}))

jest.mock('@/lib/api', () => ({
  bookings: {
    list: jest.fn()
  },
  tutors: {
    getFeatured: jest.fn()
  }
}))

describe('StudentDashboard', () => {
  it('renders welcome message with user name', async () => {
    // Given
    const user = mockUser({ role: 'student', first_name: 'John' })

    // When
    render(<StudentDashboard user={user} />)

    // Then
    expect(screen.getByText(/Welcome back, John/i)).toBeInTheDocument()
  })

  it('displays upcoming sessions section', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    (bookings.list as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, status: 'confirmed', tutor_name: 'Alice', start_time: '2025-01-21T10:00:00Z' }
      ]
    })

    // When
    render(<StudentDashboard user={mockUser()} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Upcoming Sessions')).toBeInTheDocument()
      expect(screen.getByText('Alice')).toBeInTheDocument()
    })
  })

  it('shows CTA to find tutors when no sessions', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    (bookings.list as jest.Mock).mockResolvedValue({ data: [] })

    // When
    render(<StudentDashboard user={mockUser()} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText(/Find a Tutor/i)).toBeInTheDocument()
    })
  })

  it('displays recommended tutors', async () => {
    // Given
    const { tutors } = await import('@/lib/api')
    (tutors.getFeatured as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, name: 'Bob', subject: 'Math', rating: 4.9 }
      ]
    })

    // When
    render(<StudentDashboard user={mockUser()} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Bob')).toBeInTheDocument()
      expect(screen.getByText('Math')).toBeInTheDocument()
    })
  })
})
```

**File:** `frontend/__tests__/components/dashboards/TutorDashboard.test.tsx`

```typescript
describe('TutorDashboard', () => {
  it('displays earnings summary', async () => {
    // Given
    const user = mockUser({ role: 'tutor' })
    const { bookings } = await import('@/lib/api')
    (bookings.list as jest.Mock).mockResolvedValue({
      data: [],
      meta: { total_earnings: 1250.50, sessions_completed: 25 }
    })

    // When
    render(<TutorDashboard user={user} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('$1,250.50')).toBeInTheDocument()
      expect(screen.getByText('25 sessions')).toBeInTheDocument()
    })
  })

  it('displays pending booking requests count', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    (bookings.list as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, status: 'pending' },
        { id: 2, status: 'pending' },
        { id: 3, status: 'confirmed' }
      ]
    })

    // When
    render(<TutorDashboard user={mockUser({ role: 'tutor' })} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('2 Pending Requests')).toBeInTheDocument()
    })
  })

  it('shows approve/decline buttons for pending bookings', async () => {
    // When
    render(<TutorDashboard user={mockUser({ role: 'tutor' })} />)

    // Then
    await waitFor(() => {
      expect(screen.getAllByText('Approve').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Decline').length).toBeGreaterThan(0)
    })
  })
})
```

#### 2. Booking Modal Tests

**File:** `frontend/__tests__/components/ModernBookingModal.test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ModernBookingModal } from '@/components/ModernBookingModal'

describe('ModernBookingModal', () => {
  const mockOnClose = jest.fn()
  const mockOnSubmit = jest.fn()
  const tutor = { id: 1, name: 'Alice', hourly_rate: 50 }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders subject selection dropdown', () => {
    // When
    render(
      <ModernBookingModal
        isOpen={true}
        tutor={tutor}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    )

    // Then
    expect(screen.getByLabelText('Subject')).toBeInTheDocument()
  })

  it('displays date and time picker', () => {
    // When
    render(<ModernBookingModal isOpen={true} tutor={tutor} onClose={mockOnClose} onSubmit={mockOnSubmit} />)

    // Then
    expect(screen.getByLabelText(/Date/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Time/i)).toBeInTheDocument()
  })

  it('calculates total price based on duration', async () => {
    // When
    render(<ModernBookingModal isOpen={true} tutor={tutor} onClose={mockOnClose} onSubmit={mockOnSubmit} />)

    // Select 2 hour duration
    const durationSelect = screen.getByLabelText('Duration')
    fireEvent.change(durationSelect, { target: { value: '120' } })

    // Then
    await waitFor(() => {
      expect(screen.getByText('$100.00')).toBeInTheDocument() // 50 * 2
    })
  })

  it('shows validation error for past date', async () => {
    // When
    render(<ModernBookingModal isOpen={true} tutor={tutor} onClose={mockOnClose} onSubmit={mockOnSubmit} />)

    const dateInput = screen.getByLabelText(/Date/i)
    const pastDate = '2020-01-01'
    fireEvent.change(dateInput, { target: { value: pastDate } })

    const submitButton = screen.getByText('Book Session')
    fireEvent.click(submitButton)

    // Then
    await waitFor(() => {
      expect(screen.getByText(/Date must be in the future/i)).toBeInTheDocument()
    })
  })

  it('submits booking data on form submit', async () => {
    // Given
    render(<ModernBookingModal isOpen={true} tutor={tutor} onClose={mockOnClose} onSubmit={mockOnSubmit} />)

    // Fill form
    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText(/Date/i), { target: { value: '2025-02-01' } })
    fireEvent.change(screen.getByLabelText(/Time/i), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('Duration'), { target: { value: '60' } })

    // When
    fireEvent.click(screen.getByText('Book Session'))

    // Then
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        subject_id: 1,
        start_at: expect.any(String),
        duration_minutes: 60,
        notes_student: ''
      })
    })
  })

  it('closes modal when cancel button clicked', () => {
    // Given
    render(<ModernBookingModal isOpen={true} tutor={tutor} onClose={mockOnClose} onSubmit={mockOnSubmit} />)

    // When
    fireEvent.click(screen.getByText('Cancel'))

    // Then
    expect(mockOnClose).toHaveBeenCalled()
  })
})
```

#### 3. Search and Filter Tests

**File:** `frontend/__tests__/components/TutorSearchSection.test.tsx`

```typescript
describe('TutorSearchSection', () => {
  it('renders search input', () => {
    render(<TutorSearchSection onSearch={jest.fn()} />)
    expect(screen.getByPlaceholderText(/Search by name or subject/i)).toBeInTheDocument()
  })

  it('debounces search input', async () => {
    // Given
    const mockOnSearch = jest.fn()
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // When
    const input = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(input, { target: { value: 'Math' } })

    // Then - should not call immediately
    expect(mockOnSearch).not.toHaveBeenCalled()

    // After debounce delay (500ms)
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('Math')
    }, { timeout: 600 })
  })

  it('displays subject filter dropdown', () => {
    render(<TutorSearchSection onSearch={jest.fn()} />)
    expect(screen.getByLabelText(/Subject/i)).toBeInTheDocument()
  })

  it('displays price range slider', () => {
    render(<TutorSearchSection onSearch={jest.fn()} />)
    expect(screen.getByLabelText(/Price Range/i)).toBeInTheDocument()
  })
})

describe('FilterBar', () => {
  it('applies multiple filters', async () => {
    // Given
    const mockOnFilterChange = jest.fn()
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    // When - select subject
    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: '1' } })

    // When - adjust price range
    const priceSlider = screen.getByLabelText('Max Price')
    fireEvent.change(priceSlider, { target: { value: '75' } })

    // When - select rating
    fireEvent.click(screen.getByLabelText('4+ stars'))

    // Then
    await waitFor(() => {
      expect(mockOnFilterChange).toHaveBeenCalledWith({
        subject_id: 1,
        max_price: 75,
        min_rating: 4
      })
    })
  })

  it('shows active filter count badge', () => {
    // Given
    render(<FilterBar activeFilters={{ subject_id: 1, min_rating: 4 }} onFilterChange={jest.fn()} />)

    // Then
    expect(screen.getByText('2 active')).toBeInTheDocument()
  })

  it('clears all filters when reset clicked', () => {
    // Given
    const mockOnFilterChange = jest.fn()
    render(<FilterBar activeFilters={{ subject_id: 1 }} onFilterChange={mockOnFilterChange} />)

    // When
    fireEvent.click(screen.getByText('Clear Filters'))

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({})
  })
})
```

---

### End-to-End Integration Tests (Detailed)

#### 1. Complete Student Booking Flow

**File:** `tests/e2e/test_student_booking_flow.py`

```python
import pytest
from playwright.sync_api import Page, expect

class TestStudentBookingFlow:
    """Complete E2E test for student booking journey"""

    def test_complete_student_journey(
        self,
        page: Page,
        test_student_credentials,
        test_tutor_with_availability
    ):
        """
        Test: Student registers → Searches → Books → Attends → Reviews
        """

        # Step 1: Registration
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'newstudent@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Student')  # Role selection
        page.click('button:has-text("Sign Up")')

        # Verify redirect to login
        expect(page).to_have_url('http://localhost:3000/login')

        # Step 2: Login
        page.fill('input[name="email"]', 'newstudent@test.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button:has-text("Sign In")')

        # Verify redirect to dashboard
        expect(page).to_have_url('http://localhost:3000/dashboard')
        expect(page.locator('h1')).to_contain_text('Welcome')

        # Step 3: Search for tutors
        page.click('a:has-text("Find Tutors")')
        expect(page).to_have_url('http://localhost:3000/tutors')

        # Apply filters
        page.select_option('select[name="subject"]', '1')  # Math
        page.fill('input[name="max_price"]', '75')

        # Wait for filtered results
        page.wait_for_selector('.tutor-card')

        # Verify tutor cards displayed
        tutor_cards = page.locator('.tutor-card')
        expect(tutor_cards).to_have_count_greater_than(0)

        # Step 4: View tutor profile
        tutor_cards.first.click()
        expect(page).to_have_url(r'http://localhost:3000/tutors/\d+')

        # Verify profile content
        expect(page.locator('h1')).to_contain_text(test_tutor_with_availability['name'])
        expect(page.locator('.hourly-rate')).to_be_visible()
        expect(page.locator('.reviews-section')).to_be_visible()

        # Step 5: Book session
        page.click('button:has-text("Book Session")')

        # Modal opens
        modal = page.locator('[role="dialog"]')
        expect(modal).to_be_visible()

        # Fill booking form
        modal.select_option('select[name="subject"]', '1')
        modal.fill('input[name="date"]', '2025-02-15')
        modal.select_option('select[name="time"]', '10:00')
        modal.select_option('select[name="duration"]', '60')
        modal.fill('textarea[name="notes"]', 'Looking forward to learning!')

        # Submit booking
        modal.click('button:has-text("Book Session")')

        # Verify success message
        expect(page.locator('.toast-success')).to_contain_text('Booking created')

        # Verify redirect to bookings page
        expect(page).to_have_url('http://localhost:3000/bookings')

        # Step 6: Verify booking appears in list
        booking_card = page.locator('.booking-card').first
        expect(booking_card).to_be_visible()
        expect(booking_card).to_contain_text('Pending')  # Status badge

        # Step 7: Send message to tutor
        booking_card.click('button:has-text("Message")')
        expect(page).to_have_url(r'http://localhost:3000/messages\?thread=\d+')

        # Send message
        page.fill('textarea[placeholder="Type a message"]', 'Hi! Excited for our session.')
        page.click('button[aria-label="Send message"]')

        # Verify message sent
        message_bubble = page.locator('.message-bubble').last
        expect(message_bubble).to_contain_text('Excited for our session')

        # Step 8: Tutor confirms booking (simulate via API)
        # ... (API call to confirm booking) ...

        # Refresh bookings page
        page.goto('http://localhost:3000/bookings')

        # Verify status changed to Confirmed
        expect(booking_card.locator('.status-badge')).to_contain_text('Confirmed')

        # Step 9: Join session (when within window)
        # ... (fast-forward time or use test booking in past) ...

        # Step 10: Submit review
        page.goto('http://localhost:3000/bookings')
        completed_booking = page.locator('.booking-card:has-text("Completed")').first
        completed_booking.click('button:has-text("Review")')

        # Review form
        expect(page).to_have_url(r'http://localhost:3000/bookings/\d+/review')

        # Select 5 stars
        page.click('.star-rating .star:nth-child(5)')

        # Write comment
        page.fill('textarea[name="comment"]', 'Excellent tutor! Very helpful.')

        # Submit
        page.click('button:has-text("Submit Review")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('Review submitted')

        # Verify redirect back to bookings
        expect(page).to_have_url('http://localhost:3000/bookings')

        # Verify review badge on booking
        expect(completed_booking.locator('.review-badge')).to_contain_text('Reviewed')

        # Test complete!
```

#### 2. Complete Tutor Onboarding Flow

**File:** `tests/e2e/test_tutor_onboarding_flow.py`

```python
class TestTutorOnboardingFlow:
    def test_tutor_onboarding_to_first_booking(
        self,
        page: Page,
        admin_credentials
    ):
        """
        Test: Tutor registers → Onboards → Waits approval → Accepts booking
        """

        # Step 1: Register as tutor
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'newtutor@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Tutor')  # Role selection
        page.click('button:has-text("Sign Up")')

        # Auto-login after registration
        expect(page).to_have_url('http://localhost:3000/tutor/onboarding')

        # Step 2a: Onboarding - Personal Info
        page.fill('input[name="firstName"]', 'Alice')
        page.fill('input[name="lastName"]', 'Johnson')
        page.fill('input[name="phone"]', '+1234567890')
        page.select_option('select[name="country"]', 'US')
        page.select_option('select[name="primarySubject"]', '1')  # Math
        page.fill('textarea[name="introduction"]', 'Experienced math tutor...')
        page.click('button:has-text("Next")')

        # Step 2b: Education
        page.click('button:has-text("Add Education")')
        page.fill('input[name="degree"]', 'Bachelor of Science')
        page.fill('input[name="school"]', 'MIT')
        page.fill('input[name="field"]', 'Mathematics')
        page.fill('input[name="startYear"]', '2015')
        page.fill('input[name="endYear"]', '2019')
        page.click('button:has-text("Next")')

        # Step 2c: Certifications
        page.click('button:has-text("Add Certification")')
        page.fill('input[name="certName"]', 'Teaching Certificate')
        page.fill('input[name="organization"]', 'State Board')
        page.fill('input[name="issueDate"]', '2020-01-15')
        # Upload file
        page.set_input_files('input[type="file"]', 'test_files/certificate.pdf')
        page.click('button:has-text("Next")')

        # Step 2d: Availability
        # Set Monday availability
        page.click('input[name="monday"]')  # Enable Monday
        page.fill('input[name="mondayStart"]', '09:00')
        page.fill('input[name="mondayEnd"]', '17:00')
        # Repeat for other days...
        page.click('button:has-text("Next")')

        # Step 2e: Teaching Details
        page.fill('input[name="experienceYears"]', '5')
        page.fill('textarea[name="bio"]', 'I specialize in algebra and calculus...')
        # Select subjects
        page.click('input[value="1"]')  # Math
        page.select_option('select[name="subject1Proficiency"]', 'C2')
        page.click('button:has-text("Next")')

        # Step 2f: Languages
        page.click('button:has-text("Add Language")')
        page.select_option('select[name="language"]', 'en')
        page.select_option('select[name="proficiency"]', 'C2')
        page.click('button:has-text("Next")')

        # Step 2g: Pricing
        page.fill('input[name="hourlyRate"]', '50')
        # Add package
        page.click('button:has-text("Add Package")')
        page.fill('input[name="packageName"]', '5 sessions')
        page.fill('input[name="sessionCount"]', '5')
        page.fill('input[name="packagePrice"]', '225')
        page.click('button:has-text("Next")')

        # Step 2h: Review & Submit
        expect(page.locator('h2')).to_contain_text('Review Your Profile')
        page.click('input[name="agreeTerms"]')
        page.click('button:has-text("Submit for Approval")')

        # Verify submission success
        expect(page).to_have_url('http://localhost:3000/tutor/profile/submitted')
        expect(page.locator('.status-message')).to_contain_text('under review')

        # Step 3: Admin approves profile
        # Open new page/context for admin
        admin_page = page.context.new_page()
        admin_page.goto('http://localhost:3000/login')
        admin_page.fill('input[name="email"]', admin_credentials['email'])
        admin_page.fill('input[name="password"]', admin_credentials['password'])
        admin_page.click('button:has-text("Sign In")')

        # Navigate to admin dashboard
        expect(admin_page).to_have_url('http://localhost:3000/admin')

        # Click User Management tab
        admin_page.click('button:has-text("User Management")')

        # Find pending tutor
        pending_section = admin_page.locator('.pending-tutors-section')
        tutor_row = pending_section.locator('tr:has-text("newtutor@test.com")')
        expect(tutor_row).to_be_visible()

        # Click to view profile
        tutor_row.click()

        # Review modal opens
        modal = admin_page.locator('[role="dialog"]')
        expect(modal).to_be_visible()
        expect(modal).to_contain_text('Alice Johnson')

        # Approve tutor
        modal.click('button:has-text("Approve")')

        # Verify success
        expect(admin_page.locator('.toast-success')).to_contain_text('Tutor approved')

        # Close admin page
        admin_page.close()

        # Step 4: Tutor receives notification and accesses dashboard
        # Refresh tutor page
        page.reload()

        # Navigate to dashboard
        page.goto('http://localhost:3000/dashboard')

        # Verify tutor dashboard displayed
        expect(page.locator('h1')).to_contain_text('Tutor Dashboard')
        expect(page.locator('.earnings-summary')).to_be_visible()

        # Step 5: Receive booking request (simulate via API)
        # ... create booking via API ...

        # Reload dashboard
        page.reload()

        # Verify pending request appears
        pending_requests = page.locator('.pending-requests-section')
        expect(pending_requests.locator('.booking-card')).to_have_count(1)

        # Step 6: Approve booking
        booking_card = pending_requests.locator('.booking-card').first
        booking_card.click('button:has-text("Approve")')

        # Confirm modal
        confirm_modal = page.locator('[role="dialog"]')
        confirm_modal.click('button:has-text("Confirm")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('Booking confirmed')

        # Verify booking moved to upcoming
        upcoming_section = page.locator('.upcoming-sessions-section')
        expect(upcoming_section.locator('.booking-card')).to_have_count(1)

        # Test complete!
```

#### 3. Real-Time Messaging Integration Test

**File:** `tests/e2e/test_realtime_messaging.py`

```python
class TestRealtimeMessaging:
    def test_bidirectional_messaging_with_websocket(
        self,
        page: Page,
        context: BrowserContext
    ):
        """
        Test: Two users send messages in real-time via WebSocket
        """

        # Open two browser pages (student and tutor)
        student_page = page
        tutor_page = context.new_page()

        # Login student
        student_page.goto('http://localhost:3000/login')
        student_page.fill('input[name="email"]', 'student@test.com')
        student_page.fill('input[name="password"]', 'password123')
        student_page.click('button:has-text("Sign In")')

        # Login tutor
        tutor_page.goto('http://localhost:3000/login')
        tutor_page.fill('input[name="email"]', 'tutor@test.com')
        tutor_page.fill('input[name="password"]', 'password123')
        tutor_page.click('button:has-text("Sign In")')

        # Student navigates to messages
        student_page.goto('http://localhost:3000/messages')
        expect(student_page.locator('.connection-status')).to_contain_text('Connected')

        # Student opens thread with tutor
        student_page.click('text=tutor@test.com')

        # Tutor navigates to messages
        tutor_page.goto('http://localhost:3000/messages')
        expect(tutor_page.locator('.connection-status')).to_contain_text('Connected')

        # Student sends message
        student_message = 'Hi, I have a question about tomorrow's session.'
        student_page.fill('textarea[placeholder="Type a message"]', student_message)
        student_page.click('button[aria-label="Send message"]')

        # Verify message appears in student's view
        expect(student_page.locator('.message-bubble.sent').last).to_contain_text(student_message)

        # Verify message appears in tutor's view (real-time)
        expect(tutor_page.locator('.message-bubble.received').last).to_contain_text(
            student_message,
            timeout=5000  # Wait for WebSocket delivery
        )

        # Verify unread badge appears for tutor
        expect(tutor_page.locator('.unread-badge')).to_be_visible()

        # Tutor clicks thread (marks as read)
        tutor_page.click('text=student@test.com')

        # Unread badge disappears
        expect(tutor_page.locator('.unread-badge')).not_to_be_visible()

        # Verify read receipt sent to student
        expect(student_page.locator('.message-bubble.sent').last.locator('.read-checkmark')).to_be_visible(
            timeout=3000
        )

        # Tutor sends reply
        tutor_message = 'Hi! Sure, what would you like to know?'
        tutor_page.fill('textarea', tutor_message)
        tutor_page.click('button[aria-label="Send message"]')

        # Verify reply appears in tutor's view
        expect(tutor_page.locator('.message-bubble.sent').last).to_contain_text(tutor_message)

        # Verify reply appears in student's view (real-time)
        expect(student_page.locator('.message-bubble.received').last).to_contain_text(
            tutor_message,
            timeout=5000
        )

        # Test typing indicator
        tutor_page.fill('textarea', 'I am typing...')

        # Student sees typing indicator
        expect(student_page.locator('.typing-indicator')).to_contain_text('is typing', timeout=3000)

        # Tutor stops typing (clears input)
        tutor_page.fill('textarea', '')

        # Typing indicator disappears
        expect(student_page.locator('.typing-indicator')).not_to_be_visible(timeout=4000)

        # Test message editing
        # Student edits last message
        student_last_message = student_page.locator('.message-bubble.sent').last
        student_last_message.hover()
        student_last_message.click('button[aria-label="Edit"]')

        # Edit input appears
        edit_input = student_page.locator('textarea.edit-mode')
        expect(edit_input).to_be_visible()

        # Change text
        edit_input.fill('Hi, I have a question about next week's session.')
        student_page.click('button:has-text("Save")')

        # Verify edited message
        expect(student_page.locator('.message-bubble.sent').last).to_contain_text('next week')
        expect(student_page.locator('.message-bubble.sent').last.locator('.edited-label')).to_be_visible()

        # Verify edit appears in tutor's view (real-time)
        expect(tutor_page.locator('.message-bubble.received').first).to_contain_text(
            'next week',
            timeout=3000
        )
        expect(tutor_page.locator('.message-bubble.received').first.locator('.edited-label')).to_be_visible()

        # Test message deletion
        # Student deletes message
        student_page.locator('.message-bubble.sent').last.hover()
        student_page.click('button[aria-label="Delete"]')

        # Confirm deletion
        student_page.click('button:has-text("Delete")')

        # Verify message replaced with "Message deleted"
        expect(student_page.locator('.message-bubble').last).to_contain_text('Message deleted')

        # Verify deletion reflected in tutor's view
        expect(tutor_page.locator('.message-bubble').last).to_contain_text(
            'Message deleted',
            timeout=3000
        )

        # Close tutor page
        tutor_page.close()

        # Test complete!
```

---

## Test Implementation Roadmap

### Phase 1: Critical Path Tests (Week 1-2)
**Priority: HIGH**

1. **Backend API Tests**
   - [ ] Tutor profile CRUD tests (create, update, submit, approve/reject)
   - [ ] Payment integration tests (Stripe mocks, refund scenarios)
   - [ ] Availability service tests (CRUD, conflict detection, timezone)
   - [ ] Package purchase tests (buy, use credits, expiration)

2. **Frontend Component Tests**
   - [ ] StudentDashboard component test
   - [ ] TutorDashboard component test
   - [ ] ModernBookingModal component test
   - [ ] FilterBar and search tests

3. **E2E Integration Tests**
   - [ ] Complete student booking flow (register → search → book → review)
   - [ ] Complete tutor onboarding flow (register → onboard → approval → accept)

**Deliverables:**
- 25+ new backend tests
- 10+ new frontend component tests
- 2 complete E2E flows
- Test coverage: Backend 80%, Frontend 50%

---

### Phase 2: Feature Completeness Tests (Week 3-4)
**Priority: MEDIUM**

1. **Backend API Tests**
   - [ ] Settings/preferences endpoints
   - [ ] Admin audit log tests
   - [ ] Notification delivery tests
   - [ ] WebSocket event handler tests

2. **Frontend Component Tests**
   - [ ] AdminDashboard and admin components
   - [ ] Booking cards (student/tutor views)
   - [ ] Navigation components (Navbar, Sidebar)
   - [ ] Form validation tests (all forms)

3. **E2E Integration Tests**
   - [ ] Admin user management workflow
   - [ ] Payment and refund flow (all scenarios)
   - [ ] Real-time messaging (bidirectional WebSocket)
   - [ ] Tutor availability management flow

**Deliverables:**
- 20+ new backend tests
- 15+ new frontend component tests
- 4 additional E2E flows
- Test coverage: Backend 90%, Frontend 70%

---

### Phase 3: Edge Cases and Security (Week 5)
**Priority: MEDIUM**

1. **Security Tests**
   - [ ] SQL injection attempts on all text inputs
   - [ ] XSS prevention in rich text fields
   - [ ] CSRF token validation
   - [ ] Rate limit enforcement (all endpoints)
   - [ ] Unauthorized access attempts (role switching)

2. **Edge Case Tests**
   - [ ] Concurrent booking attempts on same slot
   - [ ] Booking cancellation edge cases (exactly 12h, during session)
   - [ ] WebSocket reconnection scenarios
   - [ ] File upload size/type validation
   - [ ] Maximum pagination limits (500+ items)

3. **Error Handling Tests**
   - [ ] Network timeout simulations
   - [ ] Database connection failures
   - [ ] External service failures (Stripe, S3)
   - [ ] Invalid token scenarios

**Deliverables:**
- 15+ security tests
- 15+ edge case tests
- 10+ error handling tests
- Test coverage: Backend 95%, Frontend 85%

---

### Phase 4: Performance and Accessibility (Week 6)
**Priority: LOW**

1. **Performance Tests**
   - [ ] API response time benchmarks (< 500ms p95)
   - [ ] Database query optimization validation
   - [ ] Large dataset pagination tests
   - [ ] WebSocket message throughput

2. **Accessibility Tests**
   - [ ] Keyboard navigation (all interactive elements)
   - [ ] Screen reader compatibility (aria labels)
   - [ ] Color contrast validation (WCAG AA)
   - [ ] Form label associations

3. **Responsive Design Tests**
   - [ ] Mobile layout (375px width)
   - [ ] Tablet layout (768px width)
   - [ ] Desktop layout (1920px width)

**Deliverables:**
- 10+ performance tests
- 15+ accessibility tests
- 10+ responsive design tests
- Final test coverage: Backend 95%, Frontend 85%, E2E 100%

---

## Test Execution Strategy

### Development Workflow
1. **Pre-commit:** Run linting and unit tests
2. **PR validation:** Run full test suite (unit + integration)
3. **Pre-deploy:** Run E2E tests in staging environment
4. **Post-deploy:** Run smoke tests in production

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run frontend tests
        run: docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: docker compose -f docker-compose.test.yml up e2e-tests --abort-on-container-exit
```

### Test Environments
- **Local:** Docker Compose (docker-compose.test.yml)
- **CI:** GitHub Actions
- **Staging:** Dedicated test environment with test database
- **Production:** Smoke tests only (no data modification)

### Test Data Management
- Use **fixtures** for repeatable test data
- **Seed scripts** for local development
- **Factory patterns** for dynamic test data generation
- **Database cleanup** between test runs (pytest-postgresql, testcontainers)

---

## Success Criteria

### Quantitative Metrics
- [x] Backend API test coverage: ≥95%
- [x] Frontend component test coverage: ≥85%
- [x] E2E user flow coverage: 100% (all 6 critical flows)
- [x] All critical endpoints tested (auth, booking, payment, messaging)
- [x] Zero security vulnerabilities (auth/authorization)
- [x] API p95 response time < 500ms
- [x] All tests pass in CI/CD pipeline

### Qualitative Metrics
- [x] All user stories covered by E2E tests
- [x] Edge cases and error scenarios tested
- [x] Clear test documentation and naming
- [x] Reproducible test failures (deterministic)
- [x] Fast test execution (< 10 min for full suite)

---

## Appendix

### Test File Structure

```
backend/
├── tests/
│   ├── conftest.py                      # Shared fixtures
│   ├── test_auth.py                     # ✅ Exists
│   ├── test_bookings.py                 # ✅ Exists
│   ├── test_messages.py                 # ✅ Exists
│   ├── test_reviews.py                  # ✅ Exists
│   ├── test_notifications.py            # ✅ Exists
│   ├── test_admin.py                    # ✅ Exists
│   ├── test_students.py                 # ✅ Exists
│   ├── test_tutors_api.py               # ✅ Exists
│   ├── test_subjects.py                 # ✅ Exists
│   ├── test_security.py                 # ✅ Exists
│   ├── test_payments.py                 # ❌ NEW: Payment service tests
│   ├── test_packages.py                 # ❌ NEW: Package purchase tests
│   └── modules/
│       └── tutor_profile/
│           └── tests/
│               ├── test_services.py      # ❌ NEW: Tutor profile service tests
│               └── test_availability.py  # ❌ NEW: Availability service tests

frontend/
├── __tests__/
│   ├── components/
│   │   ├── AvatarUploader.test.tsx      # ✅ Exists
│   │   ├── Button.test.tsx              # ✅ Exists
│   │   ├── Input.test.tsx               # ✅ Exists
│   │   ├── Toast.test.tsx               # ✅ Exists
│   │   ├── ProtectedRoute.test.tsx      # ✅ Exists
│   │   ├── BookingCTA.test.tsx          # ✅ Exists
│   │   ├── NotificationBell.test.tsx    # ✅ Exists
│   │   ├── ModernBookingModal.test.tsx  # ❌ NEW
│   │   ├── TutorCard.test.tsx           # ❌ NEW
│   │   ├── TutorSearchSection.test.tsx  # ❌ NEW
│   │   ├── FilterBar.test.tsx           # ❌ NEW
│   │   └── dashboards/
│   │       ├── StudentDashboard.test.tsx # ❌ NEW
│   │       ├── TutorDashboard.test.tsx   # ❌ NEW
│   │       └── AdminDashboard.test.tsx   # ❌ NEW
│   ├── pages/
│   │   ├── login.test.tsx               # ✅ Exists
│   │   ├── register.test.tsx            # ✅ Exists
│   │   └── error-pages.test.tsx         # ✅ Exists
│   ├── hooks/
│   │   ├── useWebSocket.test.tsx        # ✅ Exists
│   │   └── useFormValidation.test.tsx   # ❌ NEW
│   └── e2e/
│       └── messaging-flow.test.tsx      # ✅ Exists

tests/
└── e2e/
    ├── test_student_booking_flow.py     # ❌ NEW
    ├── test_tutor_onboarding_flow.py    # ❌ NEW
    ├── test_admin_workflow.py           # ❌ NEW
    ├── test_payment_flow.py             # ❌ NEW
    ├── test_realtime_messaging.py       # ❌ NEW
    └── test_availability_management.py  # ❌ NEW
```

### Test Coverage Dashboard

```
Module                  Statements   Missing   Coverage
---------------------------------------------------------
backend/auth.py              125         5       96%
backend/models.py            250        15       94%
backend/main.py              180        20       89%
modules/auth/               150         10       93%
modules/bookings/           280         30       89%
modules/messages/           120         15       88%
modules/payments/            90         45       50%  ❌ Needs tests
modules/tutor_profile/      200         80       60%  ❌ Needs tests
modules/packages/            60         35       42%  ❌ Needs tests
---------------------------------------------------------
TOTAL BACKEND              1455        255       82%

Component                   Coverage
------------------------------------
frontend/components/         45%  ❌ Needs tests
frontend/pages/              60%
frontend/hooks/              50%  ❌ Needs tests
frontend/lib/                70%
------------------------------------
TOTAL FRONTEND              56%
```

---

**Document Owner:** Engineering Team
**Last Updated:** 2026-01-20
**Next Review:** After Phase 1 completion (2 weeks)

---

*This test plan is a living document and will be updated as new features are added or requirements change.*
