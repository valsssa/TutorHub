 **world-leading EdTech systems architect (Global EdTech Architecture Award)**.

Below is a **complete Booking System Spec** for a tutor marketplace—**Tutor & Student** views, backend data model, APIs, policies, notifications, payouts, security, and ready-to-build UI structure. It’s concrete, production-grade, and aligned with Preply/iTalki patterns but cleaner.

---

# 1) Scope & Roles

**Roles**

* `student`
* `tutor`
* `admin`

**Objects**

* Booking (single lesson instance)
* Package (prepaid bundle of lessons)
* Availability slot (tutor’s bookable window)
* Payout (tutor earnings & transfers)
* Payment/Refund (student charges; platform fees)
* Session Link (platform room/Zoom/etc.)
* Policy (cancellation/reschedule rules)

---

# 2) Booking State Machine (single source of truth)

**Enum `booking_status`**

* `PENDING` – created by student, not yet accepted by tutor (if tutor requires confirm)
* `CONFIRMED` – live session scheduled
* `CANCELLED_BY_STUDENT`
* `CANCELLED_BY_TUTOR`
* `NO_SHOW_STUDENT`
* `NO_SHOW_TUTOR`
* `COMPLETED`
* `REFUNDED` (terminal financial state; pairs with a *cancelled* or *completed* booking when appropriate)

**Legal transitions**

| From → To                                | Trigger                                           |
| ---------------------------------------- | ------------------------------------------------- |
| PENDING → CONFIRMED                      | Tutor confirms OR auto-confirm enabled            |
| PENDING/CONFIRMED → CANCELLED_BY_STUDENT | Student cancels (rules below)                     |
| PENDING/CONFIRMED → CANCELLED_BY_TUTOR   | Tutor cancels (rules below)                       |
| CONFIRMED → NO_SHOW_STUDENT              | Tutor reports after grace window (e.g., 10 min)   |
| CONFIRMED → NO_SHOW_TUTOR                | Student reports after grace window                |
| CONFIRMED → COMPLETED                    | Auto at end + attendance, or tutor marks complete |
| CANCELLED_* → REFUNDED                   | Automatic or admin action based on policy         |
| COMPLETED → REFUNDED                     | Exception (quality guarantee) via admin only      |

**Time guards**

* **Reschedule window** and **free-cancel window** evaluated against tutor’s timezone or student’s? → **Always student local time** for fairness; UI shows both.

---

# 3) Business Policies (sane defaults)

* **Lesson durations**: `30, 45, 60, 90` minutes (enum).
* **Trial lessons**: 30 min, discounted; 1 per tutor per student.
* **Auto-confirm**: Tutors can opt-in. If `true`, PENDING instantly → CONFIRMED.
* **Free cancellation**: Student can cancel **≥ 12h** before start → full refund/credit; `< 12h` → fee or burn credit.
* **Reschedule**: Allowed **≥ 12h**; inside 12h window, counted as cancellation as per policy.
* **Tutor cancellation penalty**: If tutor cancels **< 12h**, platform records a strike; auto-refund to student; optional compensation credit to student (e.g., $5).
* **No-show rules**:

  * Student not present within **10 min** → tutor may mark **NO_SHOW_STUDENT** (earns tutor; student loses credit).
  * Tutor not present within **10 min** → **NO_SHOW_TUTOR** (student refunded; tutor receives penalty).
* **Double-booking prevention**: optimistic lock on tutor calendar; unique index `(tutor_id, start_at)` and overlap check.
* **Grace edits**: 5-minute grace for accidental scheduling errors immediately after creation (student side) if start ≥ 24h away.

---

# 4) Data Model (PostgreSQL 17, SQLAlchemy)

## 4.1 Core Tables

### `users`

* `id PK`
* `email UNIQUE, citext`
* `role ENUM('student','tutor','admin')`
* `full_name`, `avatar_url`
* `timezone` (IANA, e.g., `Europe/Belgrade`)
* `created_at`, `updated_at`

### `tutors`

* `id PK, FK users.id`
* `hourly_rate_cents INT NOT NULL`
* `currency CHAR(3) NOT NULL` (ISO 4217)
* `auto_confirm BOOLEAN DEFAULT FALSE`
* `trial_price_cents INT NULL`
* `rating_avg NUMERIC(3,2) DEFAULT 0`
* `lessons_done INT DEFAULT 0`
* `cancellation_strikes INT DEFAULT 0`
* `payout_method JSONB` (masked last4, provider etc.)
* `is_active BOOLEAN DEFAULT TRUE`

### `students`

* `id PK, FK users.id`
* `credit_balance_cents INT DEFAULT 0` (prepaid wallet)
* `preferred_language VARCHAR(10)`

### `availabilities`

* `id PK`
* `tutor_id FK`
* `weekday SMALLINT` (0=Mon)
* `start_minute SMALLINT` (0–1439)
* `end_minute SMALLINT` (exclusive)
* `effective_from DATE`, `effective_to DATE NULL`
  *(recurring weekly windows)*

### `blackouts`

* `id PK`
* `tutor_id FK`
* `start_at TIMESTAMPTZ`
* `end_at TIMESTAMPTZ`
  *(vacation or temporary blocks)*

### `packages`

* `id PK`
* `student_id`, `tutor_id`
* `title` (e.g., “10×60m English”)
* `lesson_minutes INT` (per lesson)
* `lessons_total SMALLINT`
* `lessons_used SMALLINT DEFAULT 0`
* `price_cents INT`, `currency CHAR(3)`
* `status ENUM('ACTIVE','EXHAUSTED','REFUNDED','EXPIRED')`
* `expires_at TIMESTAMPTZ NULL`
* `created_at`

### `bookings`

* `id PK`
* `student_id FK`, `tutor_id FK`
* `package_id FK NULL`
* `lesson_type ENUM('TRIAL','REGULAR','PACKAGE')`
* `status booking_status ENUM`
* `start_at TIMESTAMPTZ` (canonical UTC)
* `end_at TIMESTAMPTZ`
* `student_tz VARCHAR(64)`, `tutor_tz VARCHAR(64)`
* `rate_cents INT NOT NULL` (agreed at booking time, snapshot)
* `currency CHAR(3)`
* `platform_fee_pct NUMERIC(5,2) NOT NULL` (snapshot)
* `platform_fee_cents INT NOT NULL` (computed, frozen)
* `tutor_earnings_cents INT NOT NULL` (computed, frozen)
* `join_url TEXT NULL` (generated after confirm)
* `notes_student TEXT NULL` (freeform prep)
* `notes_tutor TEXT NULL`
* `created_by ENUM('STUDENT','TUTOR','ADMIN')`
* `created_at`, `updated_at`
* Unique partial index to prevent overlaps:

  * `EXCLUDE USING gist (tutor_id WITH =, tstzrange(start_at, end_at) WITH &&) WHERE (status IN ('PENDING','CONFIRMED'))`

### `payments`

* `id PK`
* `booking_id FK NULL` (NULL if package/wallet top-up)
* `student_id FK`
* `amount_cents INT`, `currency CHAR(3)`
* `provider ENUM('stripe','adyen','paypal','test')`
* `provider_payment_id TEXT`
* `status ENUM('REQUIRES_ACTION','AUTHORIZED','CAPTURED','REFUNDED','FAILED')`
* `created_at`, `updated_at`

### `refunds`

* `id PK`
* `payment_id FK`
* `amount_cents INT`
* `reason ENUM('STUDENT_CANCEL','TUTOR_CANCEL','NO_SHOW_TUTOR','GOODWILL','OTHER')`
* `created_at`

### `payouts`

* `id PK`
* `tutor_id`
* `period_start DATE`, `period_end DATE`
* `amount_cents INT`
* `currency CHAR(3)`
* `status ENUM('PENDING','SUBMITTED','PAID','FAILED')`
* `transfer_reference TEXT`
* `created_at`

### `audit_logs`

* `id PK`
* `actor_user_id`, `action VARCHAR(64)` (e.g., `BOOKING_CONFIRMED`)
* `object_type VARCHAR(32)` (`booking`, `payment`, …)
* `object_id UUID`
* `ip INET`, `ua TEXT`
* `metadata JSONB`
* `created_at`

**Supporting indexes**

* `bookings (tutor_id, start_at)`
* `bookings (student_id, start_at)`
* `payments (student_id, status)`
* GIN on `audit_logs.metadata`

---

# 5) Money & Rounding

* **Single source of truth**: Store **integers in cents** only.
* **Freeze snapshots** at booking: `rate_cents`, `platform_fee_pct`, `currency`.
* **Tutor earnings**: `tutor_earnings_cents = round(rate_cents * minutes/60) - platform_fee_cents`.
* **Platform fee**: fixed percent (e.g., 20%) or graduated by tutor tier; store both percent and computed cents.
* **Refund precedence**: Refund from *captured* payment; if package credit, **restore lessons_used – 1**.
* **FX**: Charge in student currency; earnings calculated in that currency; convert to tutor payout currency at payout time (store the FX rate used then).

---

# 6) API (FastAPI style)

All responses are JSON; protected via JWT; authorization via role checks; idempotency via `Idempotency-Key` header.

## 6.1 Student APIs

### POST `/api/bookings`

Create booking.

```json
{
  "tutor_id": 412,
  "start_at": "2025-10-21T09:00:00Z",
  "duration_minutes": 30,
  "lesson_type": "TRIAL",
  "notes_student": "Interview prep",
  "use_package_id": null
}
```

**Responses**

* `201` with booking:

```json
{
  "id":"b_7e5d…",
  "status":"PENDING",
  "start_at":"2025-10-21T09:00:00Z",
  "end_at":"2025-10-21T09:30:00Z",
  "student_tz":"Europe/Belgrade",
  "tutor_tz":"Europe/London",
  "rate_cents":2250,
  "currency":"USD",
  "platform_fee_pct":20.0,
  "tutor_earnings_cents":1800
}
```

* If tutor `auto_confirm=true` → status `CONFIRMED` and `join_url` pre-generated.

### GET `/api/bookings?role=student&status=UPCOMING`

Returns **CONFIRMED** future bookings for the student.

### POST `/api/bookings/{id}/cancel`

```json
{"reason":"CHANGE_OF_PLANS"}
```

* Returns refund outcome; enforces policy windows.

### POST `/api/bookings/{id}/reschedule`

```json
{"new_start_at":"2025-10-23T09:00:00Z"}
```

### GET `/api/tutors/{tutor_id}/availability?from=2025-10-01&to=2025-10-31&duration=60`

Returns a list of **UTC slots** and helper fields:

```json
[
  {"start_at":"2025-10-21T09:00:00Z","end_at":"2025-10-21T10:00:00Z","is_bookable":true}
]
```

### POST `/api/payments/intent`

Create payment intent before booking (if pay-then-book flow).

## 6.2 Tutor APIs

### GET `/api/tutor/bookings?status=pending|upcoming|completed|cancelled`

Tutor’s list view.

### POST `/api/tutor/bookings/{id}/confirm`

Confirm pending booking (if not auto).

### POST `/api/tutor/bookings/{id}/decline`

Decline (returns credit to student).

### POST `/api/tutor/bookings/{id}/mark-no-show-student`

Allowed from 10 to 60 minutes after scheduled start.

### POST `/api/tutor/bookings/{id}/notes`

```json
{"notes_tutor": "Bring last homework"}
```

### PUT `/api/tutor/availability`

Upsert recurring weekly windows. Body:

```json
{
  "windows":[
    {"weekday":2,"start_minute":600,"end_minute":900},
    {"weekday":4,"start_minute":600,"end_minute":900}
  ],
  "effective_from": "2025-10-01",
  "effective_to": null
}
```

### POST `/api/tutor/blackouts`

Create vacation blocks.

## 6.3 Admin APIs (essentials)

* `/api/admin/bookings/{id}/refund`
* `/api/admin/policies`
* `/api/admin/payouts/run?from=2025-10-01&to=2025-10-31`
* `/api/admin/bookings/search?q=…`

---

# 7) Session Links & Attendance

**Providers**: `builtin_webrtc`, `zoom`, `gmeet`.

* On `CONFIRMED`, create `join_url` via provider service; store on `bookings`.
* Attendance pings every 15s; mark present if ≥ 5 minutes cumulative.
* Auto-complete job runs every 30 minutes to transition `CONFIRMED → COMPLETED` if end time passed and at least one participant present.

---

# 8) Notifications & Reminders

**Channels**: email, push, in-app, SMS (optional).

* **On create (PENDING)**: notify tutor to confirm (if required).
* **24h / 1h reminders** to both sides; include timezone phrase:
  “11:00–11:30 • Your Time (Europe/Belgrade)”.
* **On confirm**: send `join_url` + prep notes.
* **On reschedule/cancel**: both sides with policy result (refund/credit).
* **Post-lesson**: ask student to rate; ask tutor to leave feedback.

---

# 9) RBAC & Permissions (strict)

| Action                     | Student | Tutor                            | Admin |
| -------------------------- | ------- | -------------------------------- | ----- |
| Create booking             | ✅       |                                 | ✅     |
| Confirm booking            |        | ✅ (if pending & belongs to them) | ✅     |
| Decline booking            |        | ✅                                | ✅     |
| Cancel own booking         | ✅       |                                 | ✅     |
| Mark no-show student       |        | ✅                                | ✅     |
| Mark no-show tutor         | ✅       |                                 | ✅     |
| Edit notes (student/tutor) | ✅ own   | ✅ own                            | ✅     |
| Issue refund               |        |                                 | ✅     |
| Manage availability        |        | ✅                                | ✅     |

**All writes require**: resource ownership check + status guard.

---

# 10) Conflict Checking (exact algorithm)

When creating or rescheduling a booking:

1. Convert proposed `start_at`/`end_at` to UTC.
2. Validate it falls within **any active availability window** (expand recurring windows to concrete dates for the query range).
3. Ensure it **does not overlap** existing `PENDING`/`CONFIRMED` bookings or `blackouts` using `tstzrange` overlap query.
4. Enforce **buffer**: `min_gap_minutes = 5` around each booking (configurable).
5. If `package_id` given: verify `lessons_used < lessons_total` and lesson length matches.

---

# 11) Payouts

* **Earnings accrue** when a booking becomes `COMPLETED` or `NO_SHOW_STUDENT`.
* **Hold period**: 72h before including in payout batch (dispute window).
* **Payout batch**: weekly, every Monday 00:00 UTC.
* **CSV & transfer**: generate ledger with line items (booking id, gross, fee, net, FX if applied).
* **Failures** remain in `PENDING` with error in `transfer_reference`.

---

# 12) Security & Reliability

* **Rate limits**:

  * POST bookings: `5/min per student`
  * Confirm/Decline: `20/min per tutor`
* **Idempotency**: all POST/PUT accepts `Idempotency-Key`, stored in `audit_logs.metadata`.
* **Clock safety**: all comparisons in UTC; UI converts to local.
* **Data validation**: `duration_minutes` must match allowed enum; `start_at < end_at`; not older than now + buffer.
* **Webhooks**: `/api/webhooks/payments` signature verification (Stripe/Adyen).
* **PII**: no sensitive data in URLs; mask payment info.
* **Observability**: structured logs include `booking_id`, `user_id`, `latency_ms`; traces around create/confirm/cancel flows.
* **Back-fill cron**: repair orphan intents/payments daily.
* **GDPR**: delete request anonymizes notes and purges audit IPs older than 6 months.

---

# 13) Frontend (React + Tailwind) – file layout

```
/frontend
  /app
    /student/bookings/page.tsx              ← list with tabs: Upcoming, Completed, Cancelled
    /student/bookings/[id]/page.tsx         ← details + Join/Reschedule/Cancel
    /tutor/bookings/page.tsx                ← list with tabs: Pending, Upcoming, Completed, Cancelled
    /tutor/availability/page.tsx            ← weekly grid + blackouts
  /components/bookings
    BookingCardStudent.tsx
    BookingCardTutor.tsx
    BookingStatusBadge.tsx
    RescheduleDialog.tsx
    CancelDialog.tsx
    JoinButton.tsx
```

### BookingCardStudent (data it must render)

* Tutor avatar, name, rating
* Date + time (student timezone) + duration
* Lesson type badge
* Notes preview
* Price paid & policy hint (e.g., “Free cancel until 12h before”)
* Buttons: **Join**, **Reschedule**, **Cancel**

### BookingCardTutor

* Student avatar, level badge (if available)
* Date + time (tutor timezone)
* Notes student
* Earnings (net) and status (Pending/Confirmed)
* Buttons: **Confirm/Decline** (if pending), **Add Notes**, **Mark no-show**

---

# 14) Example: Create → Confirm → Complete (happy path)

1. Student picks `2025-10-21 11:00–11:30 Europe/Belgrade` → API receives `2025-10-21T09:00:00Z` (UTC).
2. Server checks availability & conflicts; price snapshot:

   * `rate_cents=2250`, `platform_fee_pct=20.0`, `platform_fee_cents=450`, `tutor_earnings_cents=1800`.
3. Booking stored as `PENDING` (unless tutor auto-confirm).
4. Tutor confirms → `CONFIRMED`, `join_url` generated.
5. Reminders T-24h/T-1h.
6. Attendance marks both present; end job → `COMPLETED`.
7. Earnings queued; payout Monday.

---

# 15) Example: Student Cancels inside 12h

* Booking `CONFIRMED`, start in 6h.
* Student calls `/cancel` → transition `CANCELLED_BY_STUDENT`.
* Policy engine returns: refund `0` (or partial if configured), mark **credit burned** for package.
* Notification to tutor + audit log.

---

# 16) Policy Engine Interface (extensible)

```
PolicyDecision {
  allow: boolean
  reason_code: "OK" | "WINDOW_EXPIRED" | "ALREADY_STARTED" | ...
  refund_cents: number
  tutor_compensation_cents: number
  apply_strike_to_tutor: boolean
  restore_package_unit: boolean
}
```

Called from cancel/reschedule paths with context `{ now, start_at, role, lesson_type, is_trial, has_history }`.

---

# 17) Testing Matrix (must-pass)

* Overlap prevention with concurrent POSTs (10 parallel).
* Cross-timezone reschedule correctness (America/LA ↔ Asia/Seoul).
* Payment webhook retries (idempotent).
* No-show windows (cannot mark before 10 min; cannot mark after 24h).
* Refund math (trials, packages, regular).
* Payout FX conversion snapshot.

---

# 18) Minimal DTO Schemas (TypeScript)

```ts
export type BookingStatus =
  | "PENDING" | "CONFIRMED" | "CANCELLED_BY_STUDENT" | "CANCELLED_BY_TUTOR"
  | "NO_SHOW_STUDENT" | "NO_SHOW_TUTOR" | "COMPLETED" | "REFUNDED";

export interface BookingDTO {
  id: string;
  lesson_type: "TRIAL" | "REGULAR" | "PACKAGE";
  status: BookingStatus;
  start_at: string; // ISO UTC
  end_at: string;   // ISO UTC
  student_tz: string;
  tutor_tz: string;
  rate_cents: number;
  currency: string;
  platform_fee_pct: number;
  platform_fee_cents: number;
  tutor_earnings_cents: number;
  join_url?: string;
  notes_student?: string;
  notes_tutor?: string;
  tutor: { id:number; name:string; avatar_url?:string; rating_avg:number };
  student: { id:number; name:string; avatar_url?:string; level?:string };
}
```

---

# 19) Migrations (key constraints)

* `CHECK (end_at > start_at)`
* `UNIQUE (id)`
* Partial unique/exclusion index for overlap (see above)
* `FOREIGN KEY` with `ON DELETE RESTRICT` for bookings→payments
* `payments.status` transitions enforced by CHECK via trigger function if you prefer DB-level state fidelity.

---

# 20) What the **Student** & **Tutor** Must See (recap from your screenshots)

**Student card must include**

* Tutor name/photo, lesson type, date/time in student TZ, **Join**, **Reschedule**, **Cancel**, price/credit info, policy hint.

**Tutor card must include**

* Student name/photo/level, date/time in tutor TZ, **Confirm/Decline**, **Notes**, **Mark no-show**, net earnings.

