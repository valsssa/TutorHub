-- ============================================================================
-- Migration 034: Booking Status Redesign
--
-- Implements four independent fields for booking state management:
-- - session_state: Where is the booking lifecycle? (forward-only states)
-- - session_outcome: How did it end? (outcome details)
-- - payment_state: What's the money status? (payment lifecycle)
-- - dispute_state: Is there a dispute? (dispute lifecycle)
-- ============================================================================

-- ============================================================================
-- STEP 1: ADD NEW FIELDS
-- ============================================================================

-- Rename status → session_state
ALTER TABLE bookings RENAME COLUMN status TO session_state;

-- Add session outcome field (nullable - only set when session ends)
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS session_outcome VARCHAR(30);

-- Add payment state (defaults to PENDING for new bookings)
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS payment_state VARCHAR(30) DEFAULT 'PENDING';

-- Add dispute fields
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS dispute_state VARCHAR(30) DEFAULT 'NONE';
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS dispute_reason TEXT;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS disputed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS disputed_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS resolution_notes TEXT;

-- Add cancellation tracking field (who cancelled: STUDENT, TUTOR, ADMIN, SYSTEM)
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancelled_by_role VARCHAR(20);

-- ============================================================================
-- STEP 2: DATA MIGRATION
-- ============================================================================

-- Migrate PENDING → REQUESTED
UPDATE bookings
SET session_state = 'REQUESTED',
    payment_state = 'PENDING'
WHERE session_state = 'PENDING';

-- Migrate CONFIRMED → SCHEDULED
UPDATE bookings
SET session_state = 'SCHEDULED',
    payment_state = 'AUTHORIZED'
WHERE session_state = 'CONFIRMED';

-- Migrate COMPLETED → ENDED with COMPLETED outcome
UPDATE bookings
SET session_state = 'ENDED',
    session_outcome = 'COMPLETED',
    payment_state = 'CAPTURED'
WHERE session_state = 'COMPLETED';

-- Migrate CANCELLED_BY_STUDENT → CANCELLED with NOT_HELD outcome
-- Payment state depends on timing (assume VOIDED for simplicity, can be refined)
UPDATE bookings
SET session_state = 'CANCELLED',
    session_outcome = 'NOT_HELD',
    payment_state = 'VOIDED',
    cancelled_by_role = 'STUDENT'
WHERE session_state = 'CANCELLED_BY_STUDENT';

-- Migrate CANCELLED_BY_TUTOR → CANCELLED with NOT_HELD outcome
-- Tutor cancellations always result in refund
UPDATE bookings
SET session_state = 'CANCELLED',
    session_outcome = 'NOT_HELD',
    payment_state = 'REFUNDED',
    cancelled_by_role = 'TUTOR'
WHERE session_state = 'CANCELLED_BY_TUTOR';

-- Migrate NO_SHOW_STUDENT → ENDED with NO_SHOW_STUDENT outcome
UPDATE bookings
SET session_state = 'ENDED',
    session_outcome = 'NO_SHOW_STUDENT',
    payment_state = 'CAPTURED'
WHERE session_state = 'NO_SHOW_STUDENT';

-- Migrate NO_SHOW_TUTOR → ENDED with NO_SHOW_TUTOR outcome
UPDATE bookings
SET session_state = 'ENDED',
    session_outcome = 'NO_SHOW_TUTOR',
    payment_state = 'REFUNDED'
WHERE session_state = 'NO_SHOW_TUTOR';

-- Migrate REFUNDED → ENDED with dispute resolved
UPDATE bookings
SET session_state = 'ENDED',
    session_outcome = 'COMPLETED',
    payment_state = 'REFUNDED',
    dispute_state = 'RESOLVED_REFUNDED'
WHERE session_state = 'REFUNDED';

-- ============================================================================
-- STEP 3: DROP OLD CONSTRAINTS AND ADD NEW ONES
-- ============================================================================

-- Drop old booking status constraint if exists
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS valid_booking_status;

-- Add new session_state constraint
ALTER TABLE bookings ADD CONSTRAINT valid_session_state CHECK (
    session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED', 'EXPIRED')
);

-- Add session_outcome constraint (nullable, but if set must be valid)
ALTER TABLE bookings ADD CONSTRAINT valid_session_outcome CHECK (
    session_outcome IS NULL OR session_outcome IN (
        'COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR'
    )
);

-- Add payment_state constraint
ALTER TABLE bookings ADD CONSTRAINT valid_payment_state CHECK (
    payment_state IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'REFUNDED', 'PARTIALLY_REFUNDED')
);

-- Add dispute_state constraint
ALTER TABLE bookings ADD CONSTRAINT valid_dispute_state CHECK (
    dispute_state IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED')
);

-- Add cancelled_by_role constraint (nullable)
ALTER TABLE bookings ADD CONSTRAINT valid_cancelled_by_role CHECK (
    cancelled_by_role IS NULL OR cancelled_by_role IN ('STUDENT', 'TUTOR', 'ADMIN', 'SYSTEM')
);

-- ============================================================================
-- STEP 4: CREATE INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Index for auto-transition jobs (finding bookings to transition)
CREATE INDEX IF NOT EXISTS idx_bookings_session_state_times
    ON bookings(session_state, start_time, end_time)
    WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE');

-- Index for finding expired requests (24h timeout check)
CREATE INDEX IF NOT EXISTS idx_bookings_requested_created
    ON bookings(created_at)
    WHERE session_state = 'REQUESTED';

-- Index for open disputes (admin dashboard)
CREATE INDEX IF NOT EXISTS idx_bookings_disputes_open
    ON bookings(dispute_state, disputed_at)
    WHERE dispute_state = 'OPEN';

-- Index for payment reconciliation
CREATE INDEX IF NOT EXISTS idx_bookings_payment_state
    ON bookings(payment_state)
    WHERE payment_state IN ('AUTHORIZED', 'PENDING');

-- ============================================================================
-- STEP 5: UPDATE NOT NULL CONSTRAINTS
-- ============================================================================

-- Ensure payment_state and dispute_state have values
UPDATE bookings SET payment_state = 'PENDING' WHERE payment_state IS NULL;
UPDATE bookings SET dispute_state = 'NONE' WHERE dispute_state IS NULL;

-- Add NOT NULL constraints after migration
ALTER TABLE bookings ALTER COLUMN payment_state SET NOT NULL;
ALTER TABLE bookings ALTER COLUMN dispute_state SET NOT NULL;
