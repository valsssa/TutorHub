-- Migration 029: Add owner role support
-- Purpose: Add 'owner' role to valid_role constraint and prepare for owner user creation
-- Date: 2026-01-28
-- Security: Owner role cannot be assigned via public registration (enforced at application layer)

-- Update role constraint to include 'owner'
DO $$
BEGIN
    -- Drop existing constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'valid_role'
        AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users DROP CONSTRAINT valid_role;
        RAISE NOTICE 'Dropped existing valid_role constraint';
    END IF;

    -- Add new constraint with owner role
    ALTER TABLE users
    ADD CONSTRAINT valid_role CHECK (role IN ('student', 'tutor', 'admin', 'owner'));
    RAISE NOTICE 'Added valid_role constraint with owner role';
END $$;

-- Add comment explaining the owner role
COMMENT ON CONSTRAINT valid_role ON users IS 'Valid roles: student (public registration), tutor (admin-assigned), admin (admin-assigned), owner (highest privilege, admin/owner-assigned only)';

-- Note: Default owner user will be created by application on startup (backend/main.py)
-- Note: Owner role credentials configured via environment variables:
--       DEFAULT_OWNER_EMAIL (default: owner@example.com)
--       DEFAULT_OWNER_PASSWORD (default: owner123)

-- Verify constraint was updated
DO $$
DECLARE
    constraint_def TEXT;
BEGIN
    SELECT pg_get_constraintdef(oid) INTO constraint_def
    FROM pg_constraint
    WHERE conname = 'valid_role'
    AND conrelid = 'users'::regclass;

    RAISE NOTICE 'Updated constraint definition: %', constraint_def;
END $$;

DO $$
BEGIN
    RAISE NOTICE 'Migration 029_add_owner_role completed successfully';
    RAISE NOTICE 'Owner role now available - owner user will be created on application startup';
END $$;
