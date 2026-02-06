-- Migration 050: Repair missing columns from migrations 039-041
-- Purpose: Add columns that were skipped due to duplicate migration prefixes
-- Date: 2026-02-05
--
-- This migration safely adds all columns that may be missing in existing databases.
-- Uses IF NOT EXISTS / DO $$ blocks to be idempotent.

-- =============================================================================
-- FROM MIGRATION 039: extend_on_use for pricing options
-- =============================================================================

ALTER TABLE tutor_pricing_options
ADD COLUMN IF NOT EXISTS extend_on_use BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN tutor_pricing_options.extend_on_use IS
    'When TRUE, package expiration extends by validity_days on each credit use (rolling expiry)';

ALTER TABLE student_packages
ADD COLUMN IF NOT EXISTS expiry_warning_sent BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN student_packages.expiry_warning_sent IS
    'Whether an expiration warning notification has been sent for this package';

-- =============================================================================
-- FROM MIGRATION 040: Session attendance tracking
-- =============================================================================

ALTER TABLE bookings ADD COLUMN IF NOT EXISTS tutor_joined_at TIMESTAMPTZ;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS student_joined_at TIMESTAMPTZ;

COMMENT ON COLUMN bookings.tutor_joined_at IS 'Timestamp when tutor clicked join/entered the session';
COMMENT ON COLUMN bookings.student_joined_at IS 'Timestamp when student clicked join/entered the session';

CREATE INDEX IF NOT EXISTS idx_bookings_attendance_check
    ON bookings(session_state, tutor_joined_at, student_joined_at)
    WHERE session_state = 'ACTIVE';

-- =============================================================================
-- FROM MIGRATION 041: Video provider preference
-- =============================================================================

-- Tutor profiles video provider fields
ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS preferred_video_provider VARCHAR(20) DEFAULT 'zoom';

ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS custom_meeting_url_template VARCHAR(500);

ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS video_provider_configured BOOLEAN DEFAULT FALSE;

-- Add constraint for valid provider values (drop first to avoid duplicate)
ALTER TABLE tutor_profiles DROP CONSTRAINT IF EXISTS valid_video_provider;

ALTER TABLE tutor_profiles
    ADD CONSTRAINT valid_video_provider CHECK (
        preferred_video_provider IN ('zoom', 'google_meet', 'teams', 'custom', 'manual')
    );

COMMENT ON COLUMN tutor_profiles.preferred_video_provider IS
    'Preferred video provider: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN tutor_profiles.custom_meeting_url_template IS
    'Custom meeting URL template for Teams/custom providers. Supports placeholders: {booking_id}';
COMMENT ON COLUMN tutor_profiles.video_provider_configured IS
    'Whether the video provider is properly configured and ready to use';

-- Bookings video provider fields
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS video_provider VARCHAR(20);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS google_meet_link VARCHAR(500);

COMMENT ON COLUMN bookings.video_provider IS
    'Video provider used for this booking: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN bookings.google_meet_link IS
    'Google Meet link if using Google Meet as provider';

-- =============================================================================
-- Verification
-- =============================================================================

DO $$
DECLARE
    missing_cols TEXT := '';
BEGIN
    -- Check tutor_profiles columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='tutor_profiles' AND column_name='preferred_video_provider') THEN
        missing_cols := missing_cols || 'tutor_profiles.preferred_video_provider, ';
    END IF;

    -- Check bookings columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='bookings' AND column_name='tutor_joined_at') THEN
        missing_cols := missing_cols || 'bookings.tutor_joined_at, ';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='bookings' AND column_name='video_provider') THEN
        missing_cols := missing_cols || 'bookings.video_provider, ';
    END IF;

    -- Check tutor_pricing_options columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='tutor_pricing_options' AND column_name='extend_on_use') THEN
        missing_cols := missing_cols || 'tutor_pricing_options.extend_on_use, ';
    END IF;

    IF missing_cols != '' THEN
        RAISE EXCEPTION 'Migration 050 failed - missing columns: %', missing_cols;
    END IF;

    RAISE NOTICE 'Migration 050 completed successfully: All missing columns added';
END $$;
