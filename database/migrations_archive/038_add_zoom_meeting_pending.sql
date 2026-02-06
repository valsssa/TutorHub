-- Migration: Add zoom_meeting_pending field to bookings table
-- Purpose: Flag bookings that need Zoom meeting creation retried after initial failure
-- This supports resilient Zoom integration where meeting creation failures don't block booking confirmation

-- Add the zoom_meeting_pending column
ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS zoom_meeting_pending BOOLEAN DEFAULT FALSE NOT NULL;

-- Create index for efficient querying of pending meetings in background jobs
CREATE INDEX IF NOT EXISTS idx_bookings_zoom_meeting_pending
ON bookings (zoom_meeting_pending)
WHERE zoom_meeting_pending = TRUE AND session_state IN ('SCHEDULED', 'ACTIVE');

-- Comment explaining the field
COMMENT ON COLUMN bookings.zoom_meeting_pending IS 'Flag indicating Zoom meeting creation failed and needs retry. Set to TRUE when Zoom API fails during booking confirmation.';
