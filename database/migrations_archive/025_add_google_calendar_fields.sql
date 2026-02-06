-- Migration 025: Add Google Calendar integration fields
-- Adds fields for storing Google Calendar OAuth tokens and event references

-- =============================================================================
-- 1. USERS TABLE: Add Google Calendar token storage
-- =============================================================================

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS google_calendar_access_token TEXT,
  ADD COLUMN IF NOT EXISTS google_calendar_refresh_token TEXT,
  ADD COLUMN IF NOT EXISTS google_calendar_token_expires TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS google_calendar_email VARCHAR(255),
  ADD COLUMN IF NOT EXISTS google_calendar_connected_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN users.google_calendar_access_token IS 'Google Calendar OAuth access token (encrypted in production)';
COMMENT ON COLUMN users.google_calendar_refresh_token IS 'Google Calendar OAuth refresh token for token renewal';
COMMENT ON COLUMN users.google_calendar_token_expires IS 'Expiration time of the access token';
COMMENT ON COLUMN users.google_calendar_email IS 'Email associated with connected Google Calendar';
COMMENT ON COLUMN users.google_calendar_connected_at IS 'When the calendar was connected';


-- =============================================================================
-- 2. BOOKINGS TABLE: Add Google Calendar event reference
-- =============================================================================

ALTER TABLE bookings
  ADD COLUMN IF NOT EXISTS google_calendar_event_id VARCHAR(255);

COMMENT ON COLUMN bookings.google_calendar_event_id IS 'Google Calendar event ID for this booking';


-- =============================================================================
-- 3. Migration verification
-- =============================================================================

DO $$
DECLARE
  col_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'users' AND column_name = 'google_calendar_refresh_token';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: users.google_calendar_refresh_token column not created';
  END IF;

  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'bookings' AND column_name = 'google_calendar_event_id';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: bookings.google_calendar_event_id column not created';
  END IF;

  RAISE NOTICE 'Migration 025 completed successfully: Google Calendar fields added';
END $$;
