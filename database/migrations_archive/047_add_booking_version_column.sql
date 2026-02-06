-- Migration: Add version column to bookings table for optimistic locking
-- Purpose: Prevent race conditions in booking state transitions
--
-- This migration adds a version column that is incremented on every state change,
-- enabling optimistic locking to detect concurrent modifications.

-- Add version column with default value of 1
ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Add a comment explaining the column's purpose
COMMENT ON COLUMN bookings.version IS
    'Optimistic locking version - incremented on each state transition to detect race conditions';

-- Create an index on frequently queried state + version combinations
-- This helps with the SELECT FOR UPDATE queries in background jobs
CREATE INDEX IF NOT EXISTS idx_bookings_session_state_version
ON bookings(session_state, version)
WHERE deleted_at IS NULL;

-- Rollback SQL (for reference, not automatically executed):
-- DROP INDEX IF EXISTS idx_bookings_session_state_version;
-- ALTER TABLE bookings DROP COLUMN IF EXISTS version;
