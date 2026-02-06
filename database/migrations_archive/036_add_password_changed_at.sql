-- Migration: Add password_changed_at for token security
-- Description: Adds password_changed_at timestamp to users table for JWT token invalidation
-- Author: System
-- Date: 2026-01-29

-- =============================================================================
-- UP MIGRATION
-- =============================================================================

-- Add password_changed_at column to track when password was last changed
-- This is used to invalidate JWT tokens issued before the password change
ALTER TABLE users
ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;

-- Add comment for documentation
COMMENT ON COLUMN users.password_changed_at IS 'Timestamp of last password change, used for JWT token invalidation';

-- =============================================================================
-- DOWN MIGRATION (for rollback if needed)
-- =============================================================================
-- To rollback, run:
-- ALTER TABLE users DROP COLUMN IF EXISTS password_changed_at;
