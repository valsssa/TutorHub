-- Migration: Add first_name and last_name to users table
-- Description: Make names required for all users (tutors and students)
-- Date: 2026-01-20

-- Add first_name and last_name columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);

-- Create indexes for name searches
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(first_name, last_name);

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('003', 'Add first_name and last_name to users table')
ON CONFLICT (version) DO NOTHING;
