-- Add additional fields to student_profiles table
-- Migration: 019_add_student_profile_fields.sql

ALTER TABLE student_profiles
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS interests TEXT;

-- Create index on name fields for faster searching
CREATE INDEX IF NOT EXISTS idx_student_profiles_first_name ON student_profiles(first_name);
CREATE INDEX IF NOT EXISTS idx_student_profiles_last_name ON student_profiles(last_name);
