# EduStream UX Map & Information Architecture

## Executive Summary

This document provides a complete UX map of the EduStream tutoring platform, covering all routes, user journeys, and primary actions for each role.

---

## Route Map (52 Routes Total)

### Public Routes (No Authentication Required)

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/` | `app/page.tsx` | Landing page with hero, search, testimonials | "Find a Tutor" / "Get Started" |
| `/login` | `app/(public)/login/page.tsx` | User authentication | "Sign In" |
| `/register` | `app/(public)/register/page.tsx` | New user registration | "Create Account" |
| `/tutors` | `app/tutors/page.tsx` | Browse all tutors with filters | "View Profile" / "Book" |
| `/tutors/[id]` | `app/tutors/[id]/page.tsx` | Individual tutor profile (public view) | "Book Session" |
| `/help-center` | `app/help-center/page.tsx` | FAQ and support articles | "Contact Support" |
| `/support` | `app/support/page.tsx` | Contact form | "Send Message" |
| `/terms` | `app/terms/page.tsx` | Terms of service | N/A |
| `/privacy` | `app/privacy/page.tsx` | Privacy policy | N/A |
| `/cookie-policy` | `app/cookie-policy/page.tsx` | Cookie policy | N/A |
| `/become-a-tutor` | `app/become-a-tutor/page.tsx` | Tutor recruitment | "Apply Now" |
| `/affiliate-program` | `app/affiliate-program/page.tsx` | Affiliate marketing | "Join Program" |
| `/referral` | `app/referral/page.tsx` | User referral program | "Invite Friends" |

### Student Routes

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/dashboard` | `app/dashboard/page.tsx` | Student home with upcoming sessions | "Book New Session" |
| `/profile` | `app/profile/page.tsx` | Edit student profile | "Save Changes" |
| `/bookings` | `app/bookings/page.tsx` | View all bookings | "View Details" |
| `/bookings/[id]/review` | `app/bookings/[id]/review/page.tsx` | Post-session review | "Submit Review" |
| `/tutors/[id]/book` | `app/tutors/[id]/book/page.tsx` | Book a session | "Confirm & Pay" |
| `/messages` | `app/messages/page.tsx` | Message threads | "Send Message" |
| `/packages` | `app/packages/page.tsx` | View/purchase packages | "Buy Package" |
| `/wallet` | `app/wallet/page.tsx` | Credit balance & top-up | "Top Up" |
| `/saved-tutors` | `app/saved-tutors/page.tsx` | Favorited tutors | "View Profile" |
| `/settings/*` | `app/settings/` | User settings (7 sub-routes) | "Save" |

### Tutor Routes

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/dashboard` | `app/dashboard/page.tsx` | Tutor home with bookings & earnings | "Manage Schedule" |
| `/tutor/onboarding` | `app/tutor/onboarding/page.tsx` | 5-step profile setup | "Next Step" / "Submit" |
| `/tutor/profile` | `app/tutor/profile/page.tsx` | Edit tutor profile | "Save Section" |
| `/tutor/profile/submitted` | `app/tutor/profile/submitted/page.tsx` | Confirmation after submit | "Go to Dashboard" |
| `/tutor/schedule` | `app/tutor/schedule/page.tsx` | Manage availability | "Add Time Slot" |
| `/tutor/schedule-manager` | `app/tutor/schedule-manager/page.tsx` | Advanced schedule view | "Save Schedule" |
| `/tutor/earnings` | `app/tutor/earnings/page.tsx` | Earnings analytics | "Request Payout" |
| `/tutor/earnings/edit-payout` | `app/tutor/earnings/edit-payout/page.tsx` | Configure payout method | "Save" |
| `/tutor/students` | `app/tutor/students/page.tsx` | View taught students | "View Notes" |
| `/tutor/students/edit-notes` | `app/tutor/students/edit-notes/page.tsx` | Edit student notes | "Save Notes" |
| `/tutor/rules` | `app/tutor/rules/page.tsx` | Platform guidelines | N/A |
| `/bookings` | `app/bookings/page.tsx` | Incoming/active sessions | "Accept" / "Decline" |
| `/messages` | `app/messages/page.tsx` | Student communications | "Reply" |

### Admin Routes

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/admin` | `app/admin/page.tsx` | Admin dashboard (6 tabs) | Varies by tab |

**Admin Tabs:**
1. Dashboard - Overview stats
2. User Management - Approve/manage users
3. Sessions - Monitor sessions
4. Messaging - View conversations
5. Analytics - Revenue/growth charts
6. Settings - Platform configuration

### Owner Routes

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/owner` | `app/owner/page.tsx` | Owner analytics (5 tabs) | Export Data |

**Owner Tabs:**
1. Dashboard Overview - Key metrics
2. Revenue Analytics - Financial data
3. Growth Metrics - User acquisition
4. Platform Health - System status
5. Commission Tiers - Fee management

### Settings Sub-Routes (All Roles)

| Route | Purpose | Primary CTA |
|-------|---------|-------------|
| `/settings/account` | Name, email, password | "Update Account" |
| `/settings/payments` | Payment methods | "Add Method" |
| `/settings/notifications` | Email/push preferences | "Save Preferences" |
| `/settings/locale` | Language & currency | "Save" |
| `/settings/integrations` | Connected services | "Connect" |
| `/settings/privacy` | Privacy controls | "Update Privacy" |
| `/settings/danger` | Delete account | "Delete Account" |

### New Routes (Added in UX Overhaul)

| Route | File Path | Purpose | Primary CTA |
|-------|-----------|---------|-------------|
| `/verify-email/[token]` | `app/verify-email/[token]/page.tsx` | Email verification | "Go to Dashboard" |
| `/forgot-password` | `app/forgot-password/page.tsx` | Password reset request | "Send Reset Link" |
| `/reset-password/[token]` | `app/reset-password/[token]/page.tsx` | Password reset form | "Reset Password" |
| `/notifications` | `app/notifications/page.tsx` | Full notification center | "Mark All Read" |
| `/bookings/[id]/receipt` | `app/bookings/[id]/receipt/page.tsx` | Payment receipt/invoice | "Download PDF" |
| `/bookings/[id]/dispute` | `app/bookings/[id]/dispute/page.tsx` | File dispute form | "Submit Dispute" |
| `/bookings/calendar` | `app/bookings/calendar/page.tsx` | Calendar view of bookings | "View Details" |
| `/search` | `app/search/page.tsx` | Tutor search with URL params | "View Profile" / "Book" |
| `/compare` | `app/compare/page.tsx` | Compare tutors side-by-side | "Book" / "Remove" |
| `/tutor/analytics` | `app/tutor/analytics/page.tsx` | Tutor performance analytics | "Export Data" |
| `/tutor/payouts` | `app/tutor/payouts/page.tsx` | Payout history | "Export CSV" |
| `/help` | `app/help/page.tsx` | Help center home | "Search" / "Contact" |
| `/help/[category]` | `app/help/[category]/page.tsx` | Help category with articles | "Read Article" |

### Error/Utility Routes

| Route | Purpose |
|-------|---------|
| `/unauthorized` | Access denied page |
| `/not-found` | 404 page |
| `/error` | Error boundary fallback |
| `/loading` | Global loading state |

---

## Role-Based Access Matrix

```
Route                    | Public | Student | Tutor | Admin | Owner
-------------------------|--------|---------|-------|-------|-------
/                        |   ✓    |    ✓    |   ✓   |   ✓   |   ✓
/login, /register        |   ✓    |    ✓    |   ✓   |   ✓   |   ✓
/tutors, /tutors/[id]    |   ✓    |    ✓    |   ✓   |   ✓   |   ✓
/dashboard               |   ✗    |   ✓*    |  ✓*   |  ✓*   |   ✗
/profile                 |   ✗    |    ✓    |   ✗   |   ✗   |   ✗
/tutor/*                 |   ✗    |    ✗    |   ✓   |   ✗   |   ✗
/admin                   |   ✗    |    ✗    |   ✗   |   ✓   |   ✗
/owner                   |   ✗    |    ✗    |   ✗   |   ✗   |   ✓
/bookings                |   ✗    |    ✓    |   ✓   |   ✗   |   ✗
/messages                |   ✗    |    ✓    |   ✓   |   ✓   |   ✗
/packages, /wallet       |   ✗    |    ✓    |   ✗   |   ✗   |   ✗
/settings/*              |   ✗    |    ✓    |   ✓   |   ✓   |   ✗
/saved-tutors            |   ✗    |    ✓    |   ✗   |   ✗   |   ✗

* Dashboard content varies by role
```

---

## User Journeys

### Journey 1: New Student - First Booking

```
1. Landing (/)
   └── "Get Started" CTA
        ↓
2. Register (/register)
   └── Select "Student" role
   └── Enter details
   └── "Create Account"
        ↓
3. Browse Tutors (/tutors)
   └── Apply filters (subject, price, rating)
   └── View tutor cards
   └── Click "View Profile"
        ↓
4. Tutor Profile (/tutors/[id])
   └── Review qualifications, reviews, availability
   └── Click "Book Session"
        ↓
5. Booking Page (/tutors/[id]/book)
   └── Select duration (25/50 min)
   └── Choose subject
   └── Add topic notes
   └── Confirm payment
        ↓
6. Confirmation
   └── Success message
   └── "View My Bookings"
        ↓
7. Dashboard (/dashboard)
   └── See upcoming session
   └── Countdown to session
```

**Critical Points:**
- Clear pricing display throughout
- Timezone awareness at every step
- Easy cancellation before deadline

---

### Journey 2: Tutor Onboarding

```
1. Register (/register)
   └── Select "Tutor" role
        ↓
2. Onboarding Step 1 (/tutor/onboarding)
   └── Personal info (name, country, subject, languages)
   └── Age confirmation
        ↓
3. Onboarding Step 2
   └── Profile photo upload
   └── Preview image
        ↓
4. Onboarding Step 3
   └── Teaching certifications (optional)
   └── Document upload
        ↓
5. Onboarding Step 4
   └── Education history (optional)
   └── Degree documents
        ↓
6. Onboarding Step 5
   └── Profile description (min 400 chars)
   └── "Submit for Review"
        ↓
7. Submitted Page (/tutor/profile/submitted)
   └── "Profile under review" message
   └── Estimated wait time
        ↓
8. Admin Approval (async)
        ↓
9. Email Notification
   └── Approved/Rejected
        ↓
10. Dashboard Access (/dashboard)
    └── Set availability
    └── Start receiving bookings
```

**Critical Points:**
- Progress indicator at each step
- Save progress on each step
- Clear rejection reasons if not approved

---

### Journey 3: Student Books & Completes Session

```
1. Dashboard (/dashboard)
   └── View recommended tutors
   └── Or "Find Tutor" CTA
        ↓
2. Search & Book
   └── (see Journey 1, steps 3-6)
        ↓
3. Pre-Session (/bookings)
   └── See upcoming session card
   └── Reschedule option (before deadline)
   └── Cancel option (with refund info)
        ↓
4. Session Time
   └── Join via Zoom link
   └── Or "Start Session" button
        ↓
5. Post-Session (/bookings/[id]/review)
   └── Rate tutor (1-5 stars)
   └── Write review
   └── "Submit Review"
        ↓
6. Dashboard (/dashboard)
   └── Session moves to "Past Sessions"
   └── Review visible on tutor profile
```

---

### Journey 4: Tutor Manages Booking Request

```
1. Dashboard (/dashboard)
   └── Notification: "New booking request"
        ↓
2. Bookings (/bookings)
   └── See pending request card
   └── Student info, requested time, subject
        ↓
3. Decision
   ├── Accept
   │   └── Booking confirmed
   │   └── Calendar updated
   │   └── Student notified
   │
   └── Decline
       └── Optional reason
       └── Student notified
       └── Credits/payment released
        ↓
4. Session Management
   └── View session details
   └── Message student
   └── Add private notes
        ↓
5. Post-Session
   └── Mark attendance
   └── Earnings credited
```

---

### Journey 5: Admin Approves Tutor

```
1. Admin Dashboard (/admin)
   └── See "Pending Approvals" count
        ↓
2. User Management Tab
   └── Filter: "Pending Tutors"
   └── See queue of applications
        ↓
3. Review Application
   └── View tutor profile
   └── Check documents
   └── Verify qualifications
        ↓
4. Decision
   ├── Approve
   │   └── Tutor status → approved
   │   └── Email notification sent
   │   └── Profile goes live
   │
   └── Reject
       └── Enter rejection reason
       └── Email notification sent
       └── Tutor can reapply
```

---

## Page-by-Page Specifications

### Landing Page (/)

**Purpose:** Convert visitors to users

**Sections:**
1. Hero with value proposition
2. Search bar (subject, location)
3. Featured tutors carousel
4. How it works (3 steps)
5. Testimonials
6. Trust signals (stats)
7. CTA banner

**Primary CTA:** "Find a Tutor" / "Get Started"

**Empty State:** N/A (always has content)

**Loading State:** Skeleton for featured tutors

**Mobile:** Stack sections vertically, sticky CTA button

---

### Dashboard - Student (/dashboard)

**Purpose:** Central hub for student activity

**Sections:**
1. Welcome header with stats
2. Upcoming sessions (next 3)
3. Saved tutors quick access
4. Recent activity feed
5. Recommended tutors

**Primary CTA:** "Book New Session"

**Empty States:**
- No upcoming sessions → "Find your first tutor"
- No saved tutors → "Browse tutors to save favorites"

**Loading State:** Full page skeleton

**Mobile:** Collapsible sections, bottom navigation

---

### Dashboard - Tutor (/dashboard)

**Purpose:** Manage bookings and earnings

**Sections:**
1. Status banner (profile status)
2. Today's schedule
3. Pending requests (requires action)
4. Earnings summary
5. Recent reviews

**Primary CTA:** "View Schedule" / "Accept Request"

**Empty States:**
- No pending requests → "No new requests"
- No sessions today → "Free day! Update your availability"
- Profile incomplete → "Complete profile to receive bookings"

**Loading State:** Skeleton with cards

**Mobile:** Swipe cards for requests, bottom navigation

---

### Tutor Profile - Public (/tutors/[id])

**Purpose:** Convince student to book

**Sections:**
1. Header (photo, name, rating, price)
2. About section (bio, experience)
3. Subjects & expertise
4. Education & certifications
5. Availability calendar preview
6. Reviews carousel
7. Sticky booking CTA

**Primary CTA:** "Book Session" (sticky on scroll)

**Empty States:**
- No reviews → "Be the first to review"
- No availability → "No times available - Save to favorites"

**Loading State:** Profile skeleton

**Mobile:** Tabs for sections, sticky bottom CTA

---

### Booking Page (/tutors/[id]/book)

**Purpose:** Complete booking transaction

**Sections:**
1. Tutor summary card
2. Duration selector (25/50 min)
3. Subject selector
4. Topic/notes input
5. Time slot selection
6. Price breakdown
7. Payment method
8. Confirm button

**Primary CTA:** "Confirm & Pay"

**Validation:**
- Time slot required
- Duration required
- Subject required (if multiple)

**Error States:**
- Slot no longer available
- Payment failed
- Insufficient credits

**Mobile:** Single column, sticky price summary

---

### Messages (/messages)

**Purpose:** Real-time communication

**Sections:**
1. Thread list (left panel/drawer)
2. Active conversation (right panel)
3. Message input
4. Connection status indicator

**Primary CTA:** "Send" / "New Message"

**Empty States:**
- No threads → "No messages yet. Book a session to start chatting."
- Empty thread → "Start the conversation"

**Real-time Features:**
- Typing indicators
- Read receipts
- Online status

**Mobile:** Full-screen thread list, slide to conversation

---

### Settings (/settings/*)

**Purpose:** User preferences management

**Layout:** Sidebar + content area

**Sub-pages:**
1. Account - Personal details
2. Payments - Payment methods
3. Notifications - Preferences
4. Locale - Language/currency
5. Integrations - Connected apps
6. Privacy - Data controls
7. Danger Zone - Account deletion

**Primary CTA:** "Save Changes" per section

**Mobile:** Full-width navigation, back button

---

## Navigation Structure

### Global App Shell

```
┌─────────────────────────────────────────────────────┐
│  [Logo]    Home  Tutors  Messages  [🔔] [👤 User ▼] │
├─────────────────────────────────────────────────────┤
│                                                     │
│                   Page Content                      │
│                                                     │
├─────────────────────────────────────────────────────┤
│                    [Footer]                         │
└─────────────────────────────────────────────────────┘
```

### Mobile Navigation (Student)

```
┌─────────────────────────────────────────────────────┐
│  [☰]              EduStream              [🔔] [👤]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│                   Page Content                      │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [🏠]    [🔍]    [📅]    [💬]    [⚙️]              │
│  Home   Search  Bookings Messages Settings          │
└─────────────────────────────────────────────────────┘
```

### Admin Sidebar

```
┌────────────────┬────────────────────────────────────┐
│ Admin Panel    │                                    │
├────────────────┤                                    │
│ ▸ Dashboard    │         Content Area               │
│   Users        │                                    │
│   Sessions     │                                    │
│   Messaging    │                                    │
│   Analytics    │                                    │
│   Settings     │                                    │
└────────────────┴────────────────────────────────────┘
```

---

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | 360px - 639px | Single column, bottom nav |
| Tablet | 640px - 1023px | Two columns where appropriate |
| Desktop | 1024px+ | Full layout, sidebars |

---

## Accessibility Requirements

1. **Keyboard Navigation**
   - All interactive elements focusable
   - Logical tab order
   - Escape closes modals
   - Arrow keys for menus

2. **Screen Readers**
   - Semantic HTML
   - ARIA labels on icons
   - Live regions for updates
   - Skip links

3. **Visual**
   - 4.5:1 contrast ratio minimum
   - Focus indicators
   - No color-only information
   - Resizable text

4. **Touch**
   - 44x44px minimum tap targets
   - Adequate spacing between targets
   - Swipe gestures with alternatives

---

## New Components Created (UX Overhaul)

| Component | File Path | Purpose |
|-----------|-----------|---------|
| `Breadcrumb` | `components/Breadcrumb.tsx` | Navigation hierarchy display |
| `EmptyState` | `components/EmptyState.tsx` | 11 variants for different contexts |
| `BookingSuccess` | `components/BookingSuccess.tsx` | Success confirmation modal |
| `StatusBadge` | `components/StatusBadge.tsx` | Unified status display |
| `ConfirmDialog` | `components/ConfirmDialog.tsx` | Reusable confirmation |
| `PasswordStrength` | `components/PasswordStrength.tsx` | Real-time strength meter |
| `SessionWarning` | `components/SessionWarning.tsx` | Session timeout warning |
| `ProfileCompletionMeter` | `components/ProfileCompletionMeter.tsx` | Tutor profile progress |
| `SkeletonLoader` variants | `components/SkeletonLoader.tsx` | Loading skeletons for cards, messages, etc. |

---

---

## Implementation Completeness

### All Routes Verified ✅
- All 13 new routes created and functional
- All route files confirmed to exist in filesystem
- All routes accessible and rendering correctly

### All Components Verified ✅
- Breadcrumb.tsx (4.3KB) - Navigation hierarchy
- EmptyState.tsx (8KB) - 11 context variants
- BookingSuccess.tsx (9.9KB) - Booking confirmation modal
- StatusBadge.tsx (13.4KB) - Unified status display
- ConfirmDialog.tsx (6.5KB) - Reusable confirmation
- PasswordStrength.tsx (5.8KB) - Real-time strength meter
- SessionWarning.tsx (7.3KB) - Session timeout warning
- ProfileCompletionMeter.tsx (9KB) - Tutor profile progress
- SkeletonLoader.tsx (11.9KB) - Loading skeletons

### UX Polish Complete ✅
- Horizontal overflow fixed on mobile tables
- Micro-interactions added (9 new animations)
- Terminology standardized (session/booking/lesson)
- Performance optimizations in place
- Dark mode support throughout
- 44px touch targets verified

---

*Document generated: 2026-01-30*
*Last updated: 2026-01-30*
*Version: 2.1 - UX OVERHAUL COMPLETE*
*Total Routes: 65 (52 original + 13 new)*
*All implementation verified and functional*
