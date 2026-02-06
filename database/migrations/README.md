# Database Migrations

This directory contains all SQL migrations for the EduStream database schema.

## Structure

```
migrations/
├── 001_baseline_schema.sql      # Complete consolidated schema (single source of truth)
├── 002_*.sql, 003_*.sql, ...    # Future incremental migrations
└── README.md                    # This file
```

## Overview

**`001_baseline_schema.sql`** contains the complete database schema, consolidated from the original 39 migrations (001-056). This is the single source of truth for database structure.

New schema changes should be added as new numbered migrations starting at `002_*.sql`.

## How Migrations Work

### Fresh Databases

1. PostgreSQL runs `001_baseline_schema.sql` via docker-entrypoint-initdb.d
2. Backend startup verifies `schema_migrations` table
3. Any future migrations (`002_*`, `003_*`, etc.) are applied automatically

### Existing Databases

- Backend compares `schema_migrations` table against files in `migrations/`
- Runs any unapplied migrations in order

## Creating New Migrations

1. **Number**: Use the next available number (e.g., `002_add_feature.sql`)
2. **Idempotency**: Use `IF NOT EXISTS`, `DO $$ ... END $$` blocks
3. **Verification**: Include validation queries at the end

### Template

```sql
-- Migration 002: Short description
-- Purpose: Why this migration exists
-- Date: YYYY-MM-DD

BEGIN;

-- ============================================================================
-- STEP 1: Add new columns/tables
-- ============================================================================

ALTER TABLE example ADD COLUMN IF NOT EXISTS new_column VARCHAR(50);

-- ============================================================================
-- STEP 2: Migrate existing data (if needed)
-- ============================================================================

UPDATE example SET new_column = 'default' WHERE new_column IS NULL;

-- ============================================================================
-- STEP 3: Add constraints
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'check_new_column'
    ) THEN
        ALTER TABLE example ADD CONSTRAINT check_new_column CHECK (new_column IS NOT NULL);
    END IF;
END $$;

-- ============================================================================
-- STEP 4: Create indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_example_new_column ON example(new_column);

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 002 completed successfully';
END $$;
```

## Running Migrations

### Automatic (Recommended)

Migrations run automatically when the backend starts:

```bash
make dev        # Starts backend, which applies migrations
# or
docker compose up backend
```

### Verify Migrations Applied

```bash
# Check applied migrations
docker compose exec db psql -U postgres -d authapp -c "SELECT * FROM schema_migrations ORDER BY version;"

# Run verification script
./scripts/verify-database.sh
```

## Archived Migrations

The `migrations_archive/` directory contains the original 39 migration files that were consolidated into `001_baseline_schema.sql`. These are kept for historical reference only and are never executed.

## Key Schema Features

The baseline schema includes:

- **50+ tables** covering users, tutors, students, bookings, payments, messages, notifications
- **Four-field booking status system**: session_state, session_outcome, payment_state, dispute_state
- **Booking overlap prevention** via btree_gist exclusion constraint
- **Wallet system** for platform credits
- **Fraud detection** for trial abuse prevention
- **Optimistic locking** on bookings
- **Soft delete** on most tables via `deleted_at` column

See [SOURCE_OF_TRUTH.md](../SOURCE_OF_TRUTH.md) for detailed constraint documentation.

## Rollback

Migrations do not have automatic rollback. If you need to undo a migration:

1. Write a new migration that reverses the changes
2. Test thoroughly in a non-production environment
3. For critical issues, restore from backup

## Related Documentation

- [SOURCE_OF_TRUTH.md](../SOURCE_OF_TRUTH.md) - Schema integrity documentation
- [verify-database.sh](../../scripts/verify-database.sh) - Database verification script
