# EduStream Frontend-v2 UX/UI Audit Report

**Date:** 2026-02-07
**Auditors:** 5-agent parallel audit team
**Scope:** All 100+ frontend-v2 files — every page, component, hook, validator, and API module
**Status:** Audit complete. Fix phase NOT started.

---

## Executive Summary

**182 raw findings** across 5 audit domains, deduplicated to **143 unique issues**.

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 6 | Users completely blocked from core tasks |
| HIGH | 28 | Broken/confusing features, security concerns |
| MEDIUM | 62 | Poor UX but functional, missing features |
| LOW | 47 | Polish, consistency, minor accessibility |
| **Total** | **143** | |

### Worst Affected Areas
1. **Booking flow** — form broken (datetime validation), no multi-step UX, no availability checking, no timezone handling
2. **Button `asChild`** — broken implementation used in 15+ places across the app, creates invalid HTML everywhere
3. **Real-time messaging** — WebSocket hooks exist but are NOT wired into the conversation UI
4. **Notifications** — mock data fallback, field inconsistency, filters don't work server-side
5. **10 dead-end 404 pages** — admin/owner nav links to pages that don't exist
6. **Settings forms** — infinite re-render bugs in notifications and video settings

---

## TIER 1: CRITICAL (6 issues) — Users Cannot Complete Core Tasks

### C1. Booking form has no past-date validation
- **File:** `lib/validators/booking.ts:6-9`
- **Impact:** Users can book sessions in the past. Zod schema only checks `!isNaN(Date.parse(val))` but never verifies date is in the future.
- **Fix:** Add `.refine((val) => new Date(val) > new Date(), 'Date must be in the future')`. Set `min` attribute on the datetime-local input.

### C2. Booking form is a single overwhelming page, not a multi-step flow
- **File:** `app/(dashboard)/bookings/new/page.tsx:107-429`
- **Impact:** All steps (tutor, subject, date/time, message, summary) render simultaneously. No progress indicator, no step navigation, no per-step validation. Extremely overwhelming on mobile.
- **Fix:** Implement stepper with 4 steps: Select Tutor → Select Subject → Date/Time → Review & Confirm. Add progress bar and Next/Back buttons.

### C3. Login page redirect ignores `?redirect=` parameter
- **File:** `app/(auth)/login/page.tsx:44-50`
- **Impact:** Users clicking deep links (bookings, messages, settings) get redirected to login, then always land on their role dashboard instead of their intended destination.
- **Fix:** Read `searchParams.get('redirect')`, use as post-login destination. Validate the URL is relative to prevent open redirect.

### C4. 404 page "Go back" button uses `javascript:` protocol in Next.js Link (XSS + non-functional)
- **File:** `app/not-found.tsx:30`
- **Impact:** `<Link href="javascript:history.back()">` is a potential XSS vector and may not execute in Next.js App Router. The "Go back" button is completely non-functional.
- **Fix:** Replace with `<button onClick={() => window.history.back()}>`.

### C5. Registration does not handle "email already exists" gracefully
- **File:** `app/(auth)/register/page.tsx:34-46`
- **Impact:** Generic error shown with no link to login. Dead-end experience for users who already have an account.
- **Fix:** Detect "already exists" error, show: "An account with this email already exists. [Sign in instead](/login)."

### C6. Notification settings `useEffect` with `form` in deps causes infinite re-renders
- **File:** `app/(dashboard)/settings/notifications/page.tsx:148`
- **Impact:** The `form` object from `useForm()` is a new reference every render. Including it in `useEffect` deps causes infinite loop — CPU spinning, flashing UI, potential browser hang.
- **Fix:** Remove `form` from the dependency array (use eslint-disable comment like other settings pages).

---

## TIER 2: HIGH (28 issues) — Broken/Confusing Features

### User Flow & Navigation

**H1.** 10 sidebar/quick-action nav links lead to nonexistent pages (404)
- **Files:** `sidebar.tsx:58-69`, `admin/page.tsx:466`, `owner/page.tsx:558-597`
- **Routes:** `/admin/users`, `/admin/approvals`, `/admin/reports`, `/admin/tutors`, `/owner/analytics`, `/owner/admins`, `/owner/financial`, `/owner/config`, `/owner/reports/financial`, `/owner/settings`
- **Fix:** Create "Coming Soon" placeholder pages, or hide nav items until built.

**H2.** Notification bell always shows red dot regardless of actual unread count
- **File:** `components/layouts/topbar.tsx:89`
- **Fix:** Fetch unread count, show badge conditionally. Show count number.

**H3.** Button `asChild` implementation does not forward loading/disabled states
- **File:** `components/ui/button.tsx:49-55`
- **Impact:** Used in 15+ places. When `asChild` is true, loading spinner is skipped. HTML button attributes leak onto `<a>` tags. Creates invalid HTML (interactive element inside interactive element) at every `<Link>` wrapper.
- **Fix:** Implement properly using Radix Slot pattern, or document asChild as styling-only and fix all usages.

**H4.** All landing page CTA buttons use `<Link><Button>` (invalid nested interactive HTML)
- **File:** `app/page.tsx:96-98,119-124,125-129,254-263,278-283`
- **Fix:** Use `<Button asChild><Link>` pattern or style Link directly with buttonVariants().

**H5.** Tutor dashboard buttons also nest `<Link>` inside `<Button>` (5 instances)
- **File:** `app/(dashboard)/tutor/page.tsx:359-364,494-523`
- **Fix:** Same as H4.

### Messaging

**H6.** Real-time messages NOT wired into conversation page — WebSocket hooks exist but unused
- **File:** `app/(dashboard)/messages/[conversationId]/page.tsx`
- **Impact:** New messages don't appear until manual refresh. Defeats purpose of chat.
- **Fix:** Import and use `useRealtimeMessages`. Wire `onNewMessage` to append to message list.

**H7.** No WebSocket connection status indicator anywhere in UI
- **File:** `app/(dashboard)/messages/[conversationId]/page.tsx`
- **Fix:** Add connection banner (e.g., "Reconnecting..." with spinner).

**H8.** No offline message queuing — WebSocket `send()` returns false silently when disconnected
- **File:** `lib/hooks/use-websocket.ts:237-249`
- **Fix:** Add message queue that replays on reconnect.

### Notifications

**H9.** Notification `type` filter not sent to backend API — filter buttons do nothing server-side
- **File:** `lib/api/notifications.ts:12-18`
- **Fix:** Add `if (filters?.type) params.type = filters.type;` to API function.

**H10.** `is_read` vs `read` field inconsistency — different components use opposite priority
- **Files:** `notification-item.tsx:46`, `notification-bell.tsx:99`, `notifications/page.tsx:86`
- **Fix:** Standardize on one field name. Add normalizer at API layer.

**H11.** Double filtering bug — client filters applied on top of (broken) server filter
- **File:** `app/(dashboard)/notifications/page.tsx:78-91`
- **Fix:** Choose one: server-side only or client-side only.

### Booking & Tutor Profile

**H12.** Booking form loads all 100 tutors at once with no search
- **File:** `app/(dashboard)/bookings/new/page.tsx:51`
- **Fix:** Add search input or paginated loading.

**H13.** No availability checking in booking form — users can pick any time regardless of tutor schedule
- **File:** `app/(dashboard)/bookings/new/page.tsx:253-258`
- **Fix:** Fetch tutor availability, show available slots.

**H14.** No timezone handling — datetime-local value sent directly, no UTC conversion
- **File:** `app/(dashboard)/bookings/new/page.tsx:253-258`
- **Fix:** Display user timezone, convert to UTC before API call.

**H15.** Booking form rating uses asterisks `*****` instead of star icons
- **File:** `app/(dashboard)/bookings/new/page.tsx:174`
- **Fix:** Use `StarRating` component or `Star` icon.

**H16.** "Join Session" button on booking detail has no href or onClick — does nothing
- **File:** `app/(dashboard)/bookings/[id]/page.tsx:261-265`
- **Fix:** Link to `booking.join_url`.

**H17.** "Request Reschedule" button has no functionality
- **File:** `app/(dashboard)/bookings/[id]/page.tsx:268-272`
- **Fix:** Implement reschedule modal using `useRescheduleBooking` hook.

**H18.** "Load more reviews" replaces reviews instead of appending
- **File:** `app/(dashboard)/tutors/[id]/page.tsx:438-445`
- **Fix:** Use `useInfiniteQuery` or accumulate pages in local state.

**H19.** All reviewer names hardcoded as "Student" on tutor profile
- **File:** `app/(dashboard)/tutors/[id]/page.tsx:418-420`
- **Fix:** Use actual reviewer name from review data.

**H20.** Sessions count falls back to review count (semantically wrong)
- **File:** `app/(dashboard)/tutors/[id]/page.tsx:491`
- **Fix:** Show "N/A" if `total_sessions` unavailable, don't fall back to reviews.

**H21.** Packages page uses `?tutor_id=` but booking form reads `?tutor=` — pre-selection broken
- **File:** `app/(dashboard)/tutors/[id]/packages/page.tsx:313`
- **Fix:** Standardize on `?tutor=`.

### Wallet

**H22.** No withdrawal UI for tutors — types exist but no page/form
- **Files:** `app/(dashboard)/wallet/page.tsx`, `types/wallet.ts:83-118`
- **Fix:** Build withdrawal UI with bank account management.

**H23.** Wallet top-up has no max amount validation, silent failure on invalid amounts
- **File:** `app/(dashboard)/wallet/page.tsx:36-39`
- **Fix:** Add min/max validation with error messages and preset amount buttons.

### Settings & Profile

**H24.** Video settings also has `form` in useEffect deps — same infinite re-render bug
- **File:** `app/(dashboard)/settings/video/page.tsx:144-151`
- **Fix:** Remove `form` from dependency array.

**H25.** Profile edit "Upload Photo" button is non-functional (no onClick)
- **File:** `app/(dashboard)/profile/edit/page.tsx:104-111,241-248`
- **Fix:** Wire up file upload or remove the button.

**H26.** Tutor edit form silently discards hourly_rate and subject_ids changes
- **File:** `app/(dashboard)/profile/edit/page.tsx:204-219`
- **Fix:** Include in API call or remove fields from form.

**H27.** Admin tutor rejection uses `window.prompt()` and `alert()`
- **File:** `app/(dashboard)/admin/page.tsx:266-269`
- **Fix:** Use custom modal component.

### Security

**H28.** Forgot password may reveal whether email is registered (email enumeration)
- **File:** `app/(auth)/forgot-password/page.tsx:23-34`
- **Fix:** Always show success state regardless of email existence.

---

## TIER 3: MEDIUM (62 issues) — Poor UX but Functional

### Forms & Validation (12)
| # | Issue | File |
|---|-------|------|
| M1 | Password hint disappears when error shows (hint replaced by error) | `components/ui/input.tsx:41-43` |
| M2 | No loading/disabled state on role buttons during registration submit | `register/page.tsx:62-88` |
| M3 | Password validation reveals requirements one at a time (sequential) | `lib/validators/auth.ts:8-13` |
| M4 | Reset password doesn't verify token before showing form | `reset-password/[token]/page.tsx:12-48` |
| M5 | Input missing `aria-describedby` for errors/hints | `components/ui/input.tsx:11-48` |
| M6 | Input missing `aria-invalid` when error present | `components/ui/input.tsx:26-39` |
| M7 | Notification settings push/email toggles share same backing field | `settings/notifications/page.tsx:238-306` |
| M8 | No unsaved changes warning on settings page navigation | All settings pages |
| M9 | Duplicate notification schemas with different field names | `settings/notifications/page.tsx:21-28` vs `validators/settings.ts:39-47` |
| M10 | Auth validator password requirements shown only after submission | `lib/validators/auth.ts:8-13` |
| M11 | Booking form submit button doesn't check for start_time | `bookings/new/page.tsx:398` |
| M12 | Student notes no character limit enforcement (maxLength) on textarea | `tutor/students/[studentId]/notes/page.tsx:185` |

### Navigation & Layout (11)
| # | Issue | File |
|---|-------|------|
| M13 | Auth layout brand "EduStream" is not a link back to home | `app/(auth)/layout.tsx` |
| M14 | Register page does not redirect already-authenticated users | `register/page.tsx` |
| M15 | Forgot password page does not redirect authenticated users | `forgot-password/page.tsx` |
| M16 | Card double padding on auth pages (Card + CardContent both padded) | `components/ui/card.tsx:13` + auth pages |
| M17 | Settings sidebar button `absolute bottom-4` may overlap nav items | `sidebar.tsx:155` |
| M18 | Placeholder nav items render identically to real items | `sidebar.tsx:33,58-69` |
| M19 | Mobile sidebar has no explicit close (X) button | `sidebar.tsx:116-127` |
| M20 | Mobile sidebar may stay open after browser back navigation | `sidebar.tsx:138` |
| M21 | Topbar `kbd` element uses `hidden sm:inline-flex` (known problematic pattern) | `topbar.tsx:58` |
| M22 | Topbar "Profile" link goes to dashboard for admin/owner roles | `topbar.tsx:34-39` |
| M23 | Auth flash before redirect in dashboard layout | `app/(dashboard)/layout.tsx:17-36` |

### Booking & Tutors (11)
| # | Issue | File |
|---|-------|------|
| M24 | No confirmation dialog before booking submission | `bookings/new/page.tsx:393-401` |
| M25 | No success toast after booking creation | `bookings/new/page.tsx:100-103` |
| M26 | Tutor search only by subject, not by tutor name | `tutors/page.tsx:43-44` |
| M27 | No rating filter on tutor search | `tutors/page.tsx` |
| M28 | Mobile filter toggle doesn't show active filter count | `tutors/page.tsx:91-98` |
| M29 | "Highest Price" sort option missing | `tutors/page.tsx:26-30` |
| M30 | Share button on tutor profile has no functionality | `tutors/[id]/page.tsx:256-258` |
| M31 | Tutor availability shows no timezone label | `tutors/[id]/page.tsx:338-366` |
| M32 | Video embed fallback accepts arbitrary URLs (potential XSS) | `tutors/[id]/page.tsx:59-99` |
| M33 | Booking list has no pagination | `bookings/page.tsx:168-177` |
| M34 | Booking list tab counts not shown | `bookings/page.tsx:96-108` |

### Messaging & Notifications (10)
| # | Issue | File |
|---|-------|------|
| M35 | Message input is single-line `<input>`, not `<textarea>` | `message-input.tsx:45-59` |
| M36 | No typing indicators shown in UI | `messages/[conversationId]/page.tsx` |
| M37 | No online/offline status on conversation header | `messages/[conversationId]/page.tsx:208-215` |
| M38 | ConversationListItem `isActive` prop never passed | `messages/page.tsx:155-160` |
| M39 | No pagination on notifications page | `notifications/page.tsx:78-79` |
| M40 | No error state on notifications page (shows empty state on failure) | `notifications/page.tsx:78,168-186` |
| M41 | Notification bell dropdown lacks keyboard accessibility | `notification-bell.tsx:60-114` |
| M42 | Conversation page height breaks on mobile with virtual keyboard | `messages/[conversationId]/page.tsx:168,179` |
| M43 | No back button on messages list page (mobile) | `messages/page.tsx` |
| M44 | WebSocket auto-connects on every page, not just messaging | `use-websocket.ts:286-301` |

### Wallet & Favorites (8)
| # | Issue | File |
|---|-------|------|
| M45 | Wallet balance not auto-refreshed after Stripe redirect | `use-wallet.ts:13-18` |
| M46 | No success/cancel handling after Stripe checkout return | `wallet/page.tsx` |
| M47 | No preset quick-add amount buttons for wallet top-up | `wallet/page.tsx:146-188` |
| M48 | Transaction amount sign logic could break on negative amounts | `transaction-item.tsx:75-78` |
| M49 | No pagination on favorites page | `favorites/page.tsx` |
| M50 | Remove favorite has no undo/confirmation | `favorites/page.tsx:124-137` |
| M51 | Favorites error retry uses `window.location.reload()` instead of refetch | `favorites/page.tsx:54` |
| M52 | Favorite card renders empty ghost div when tutor is null | `favorites/page.tsx:121-123` |

### Profile & Settings (7)
| # | Issue | File |
|---|-------|------|
| M53 | Profile review count uses 3 different field names inconsistently | `profile/page.tsx:141,191,209` |
| M54 | Student profile is sparse (no bio, no stats, no booking history) | `profile/page.tsx:261-351` |
| M55 | Profile edit bio always resets to empty for students | `profile/edit/page.tsx:67,75` |
| M56 | Availability grid has no overlap detection for time slots | `availability-grid.tsx:51-62` |
| M57 | Availability grid end time dropdown shows all options (no filtering) | `availability-grid.tsx:148-169` |
| M58 | Availability timezone not saved to backend | `profile/availability/page.tsx:115-129` |
| M59 | Integrations disconnect uses `window.confirm()` instead of modal | `settings/integrations/page.tsx:278` |

### Dashboards (3)
| # | Issue | File |
|---|-------|------|
| M60 | Student dashboard wallet/package stats hardcoded to $0/0 | `student/page.tsx:91-92` |
| M61 | Student dashboard "View" button on session cards does nothing | `student/page.tsx:139` |
| M62 | Tutor dashboard performance metrics are hardcoded (95% completion) | `tutor/page.tsx:563-564` |

---

## TIER 4: LOW (47 issues) — Polish & Minor Items

### Accessibility (10)
- L1: Error messages lack ARIA live regions (`role="alert"`) — auth forms
- L2: Auth heading structure (`<h1>` for brand, `<h2>` for form title)
- L3: No `aria-busy` on Button loading state
- L4: Star rating has no keyboard arrow navigation between stars
- L5: Review form default rating 0 has no visual error indication
- L6: Skeleton components lack `aria-busy="true"` and `role="status"`
- L7: Owner dashboard period selector has no `aria-label`
- L8: Search recent removal button invisible on touch devices (hover-only)
- L9: Feature cards on landing page have hover states but aren't interactive
- L10: Theme toggle has no tooltip explaining current state

### Visual Consistency (12)
- L11: Verify email page uses raw SVG instead of Lucide components
- L12: Verify email "Sign in" is a styled link, not Button component
- L13: Card has no border by default (relies on shadow alone)
- L14: Button focus ring has no dark mode offset color
- L15: Wallet subtitle missing dark mode text color
- L16: Notes textarea uses `rounded-lg` instead of `rounded-xl`
- L17: Select dropdowns on transactions page not styled consistently
- L18: 404 page has no Card wrapping (unlike auth pages)
- L19: Messages quick action uses Calendar icon instead of MessageSquare
- L20: Loading page has no branding (just spinner + text)
- L21: Dashboard loading skeleton double-padding with AppShell
- L22: Owner Recharts tooltip uses CSS variable that may not exist

### Data Integrity (8)
- L23: Landing page stats are hardcoded fake numbers (500+ tutors etc.)
- L24: Student dashboard bookings query uses `status: 'confirmed'` (may mismatch API)
- L25: Tutor earnings calculation multiplies ALL-TIME sessions by current rate
- L26: Response rate shows "Active"/"100%" (meaningless metric)
- L27: Session duration hardcoded as "60 min" in pending request card
- L28: Search subject results show `tutor_count: 0` (hardcoded)
- L29: Owner chart bars all same color (fill not mapped from data)
- L30: Message bubble timestamp styling ternary is dead code

### Missing Features (8)
- L31: Landing page footer missing Privacy Policy/Terms/Contact links
- L32: No "Resend verification email" on verify-email error state
- L33: Dark mode no manual toggle on auth/landing pages
- L34: No search/filter on favorites page
- L35: Tutor subject badges limited to 8 with no "show more"
- L36: Availability grid has no "copy day" shortcut
- L37: Availability grid has no total weekly hours summary
- L38: No "select all"/"clear all" on subject selector dropdown

### Minor Code Issues (9)
- L39: Registration name fields have no placeholder text
- L40: Confirm password field missing `autocomplete` attribute
- L41: Login could show multiple success banners simultaneously
- L42: Booking list date filters don't clear on tab switch
- L43: "New Booking" button shown to tutors (should be student-only)
- L44: Bio character limit mismatch: 500 (settings) vs 1000 (profile edit)
- L45: OAuth callback params remain in URL permanently
- L46: UI store has dead `sidebarOpen`/`toggleSidebar` code
- L47: Avatar lazy loading not set on `<img>`

---

## Fix Roadmap (Recommended Priority Order)

### Sprint 1: Critical Blockers (6 issues)
1. C1 — Booking form past-date validation
2. C4 — 404 page `javascript:` XSS fix
3. C6 — Notification settings infinite re-render
4. H24 — Video settings infinite re-render
5. C3 — Login redirect preserve intended destination
6. C5 — Registration "email exists" graceful handling

### Sprint 2: Core Feature Fixes (12 issues)
7. H3/H4/H5 — Button `asChild` implementation + all usages (15+ files)
8. H6 — Wire real-time messages into conversation page
9. H16 — Join Session button functionality
10. H17 — Reschedule button functionality
11. C2 — Booking form multi-step redesign
12. H13 — Booking form availability checking
13. H14 — Timezone handling in booking form
14. H9/H10/H11 — Notification filter + field consistency fixes
15. H2 — Notification bell conditional badge
16. H1 — Create placeholder pages for 10 dead-end nav links

### Sprint 3: UX Improvements (15 issues)
17. H19 — Reviewer names on tutor profile
18. H18 — Reviews load-more append (not replace)
19. H20 — Sessions count fallback fix
20. H21 — Packages page query param fix
21. H25 — Upload photo button
22. H26 — Tutor edit form save all fields
23. H22 — Wallet withdrawal UI for tutors
24. M35 — Message input → textarea
25. M45/M46 — Stripe redirect handling
26. M60/M61 — Student dashboard real data + View button
27. M62 — Tutor dashboard real metrics
28. H27 — Admin rejection modal (replace window.prompt)
29. H28 — Email enumeration fix on forgot password
30. M24/M25 — Booking confirmation dialog + success toast

### Sprint 4: Accessibility & Polish (remaining)
- All MEDIUM accessibility items (M5, M6, M41, etc.)
- All LOW polish items
- Remaining MEDIUM UX items

---

## Findings by File (Quick Reference)

| File | Issue Count | Highest Severity |
|------|-------------|-----------------|
| `bookings/new/page.tsx` | 11 | CRITICAL |
| `components/ui/button.tsx` | 6 | HIGH |
| `tutors/[id]/page.tsx` | 7 | HIGH |
| `settings/notifications/page.tsx` | 5 | CRITICAL |
| `messages/[conversationId]/page.tsx` | 6 | HIGH |
| `topbar.tsx` | 5 | HIGH |
| `sidebar.tsx` | 7 | HIGH |
| `bookings/[id]/page.tsx` | 5 | HIGH |
| `wallet/page.tsx` | 5 | HIGH |
| `profile/edit/page.tsx` | 4 | HIGH |
| `notifications/page.tsx` | 5 | HIGH |
| `app/page.tsx` (landing) | 5 | HIGH |
| `student/page.tsx` | 6 | MEDIUM |
| `tutor/page.tsx` | 7 | HIGH |
| `admin/page.tsx` | 4 | HIGH |
| `owner/page.tsx` | 5 | MEDIUM |
| `favorites/page.tsx` | 5 | MEDIUM |

---

## Cross-Reference with Previous Bug Hunt (2026-02-06)

Issues confirmed by BOTH the bug hunt and this UX audit:
- Button `asChild` not implemented → confirmed, affects 15+ files
- Booking form Zod datetime broken → confirmed + additional past-date issue found
- Login redirect ignores role → confirmed (login always to `/student`) + redirect param issue
- Mock notifications as real data → confirmed + additional filter/field bugs found
- Heart button non-functional → confirmed in tutor profile
- `useEffect` with `form` in deps → confirmed in notifications + video settings
- Operator precedence bug → confirmed in profile stats
- Owner `hidden sm:inline` → confirmed already fixed to `max-sm:hidden`
- Notification `is_read` vs `read` → confirmed with additional inconsistency details
- `PurchasedPackageStatus` mismatch → confirmed with switch case evidence

**NEW issues found by this audit (not in bug hunt):**
- 10 dead-end 404 pages from nav
- Real-time messaging not wired in
- No WebSocket status indicator
- Booking form has no multi-step UX
- No availability checking in booking form
- No timezone handling in booking form
- Wallet has no withdrawal UI
- No Stripe redirect handling
- Student dashboard stats hardcoded
- Multiple button nesting violations
- Profile edit silently discards tutor fields
- Availability timezone not saved
- 404 page XSS via javascript: protocol
- And 50+ more UX/accessibility issues
