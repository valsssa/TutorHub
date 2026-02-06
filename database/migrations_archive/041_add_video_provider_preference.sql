-- Migration 041: Add video meeting provider preference for tutors
-- Enables tutors to select their preferred video conferencing provider

-- =============================================================================
-- 1. TUTOR_PROFILES TABLE: Add video provider preference fields
-- =============================================================================

-- Video provider preference (zoom, google_meet, teams, custom)
ALTER TABLE tutor_profiles
  ADD COLUMN IF NOT EXISTS preferred_video_provider VARCHAR(20) DEFAULT 'zoom';

-- Custom meeting URL template for Teams, custom providers
-- Supports placeholder: {booking_id}, {tutor_name}, {student_name}
ALTER TABLE tutor_profiles
  ADD COLUMN IF NOT EXISTS custom_meeting_url_template VARCHAR(500);

-- Flag to indicate if provider is properly configured
ALTER TABLE tutor_profiles
  ADD COLUMN IF NOT EXISTS video_provider_configured BOOLEAN DEFAULT FALSE;

-- Add constraint for valid provider values
ALTER TABLE tutor_profiles
  DROP CONSTRAINT IF EXISTS valid_video_provider;

ALTER TABLE tutor_profiles
  ADD CONSTRAINT valid_video_provider CHECK (
    preferred_video_provider IN ('zoom', 'google_meet', 'teams', 'custom', 'manual')
  );

COMMENT ON COLUMN tutor_profiles.preferred_video_provider IS 'Preferred video provider: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN tutor_profiles.custom_meeting_url_template IS 'Custom meeting URL template for Teams/custom providers. Supports placeholders: {booking_id}';
COMMENT ON COLUMN tutor_profiles.video_provider_configured IS 'Whether the video provider is properly configured and ready to use';


-- =============================================================================
-- 2. BOOKINGS TABLE: Add video provider tracking
-- =============================================================================

-- Track which provider was used for each booking
ALTER TABLE bookings
  ADD COLUMN IF NOT EXISTS video_provider VARCHAR(20);

-- Google Meet specific fields (separate from calendar event)
ALTER TABLE bookings
  ADD COLUMN IF NOT EXISTS google_meet_link VARCHAR(500);

COMMENT ON COLUMN bookings.video_provider IS 'Video provider used for this booking: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN bookings.google_meet_link IS 'Google Meet link if using Google Meet as provider';


-- =============================================================================
-- 3. Migration verification
-- =============================================================================

DO $$
DECLARE
  col_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'tutor_profiles' AND column_name = 'preferred_video_provider';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: tutor_profiles.preferred_video_provider column not created';
  END IF;

  SELECT COUNT(*) INTO col_count
  FROM information_schema.columns
  WHERE table_name = 'bookings' AND column_name = 'video_provider';

  IF col_count = 0 THEN
    RAISE EXCEPTION 'Migration failed: bookings.video_provider column not created';
  END IF;

  RAISE NOTICE 'Migration 041 completed successfully: Video provider preference fields added';
END $$;
