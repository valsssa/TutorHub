# Database Migrations

This directory contains all SQL migrations for the EduStream database schema.

## Overview

Migrations are applied automatically during backend startup via the migration runner. Each migration is idempotent (safe to re-run) and includes its own verification logic.

## Migration Numbering

Migrations are numbered sequentially (001, 002, etc.). Note that there is a **gap in numbering from 006-020**:

| Number Range | Status | Notes |
|--------------|--------|-------|
| 001-005 | Active | Initial message and user enhancements |
| 006-020 | Archived | Moved to `migrations_archive/` for historical reference |
| 021-050+ | Active | Current schema evolution |

The gap exists because migrations 006-020 were consolidated into `init.sql` during a schema refactoring effort and archived for reference.

## Migration List

### Active Migrations

| Migration | Purpose |
|-----------|---------|
| 001 | Add message tracking columns (read_at, is_edited, edited_at, updated_at) |
| 002 | Add message attachments support |
| 003 | Add user first_name/last_name columns |
| 004 | Update booking status constraint (legacy, superseded by 034) |
| 005 | Add teaching philosophy to tutor profiles |
| 023 | Add subject categories |
| 024 | Add integration fields (Zoom, OAuth) |
| 025 | Add Google Calendar integration fields |
| 026 | Add timezone validation |
| 027 | Add validity_days to pricing options |
| 028 | Create student_notes table |
| 029 | Add owner role |
| 030 | **Standardize currency fields** - VARCHAR(3), ISO 4217 format checks |
| 031 | **Add performance indexes** - Conversation, booking, package queries |
| 032 | Add tutor search (full-text) |
| 033 | **Add package consistency check** - sessions_remaining = purchased - used |
| 034 | **Booking status redesign** - Four-field status system |
| 035 | **Add booking overlap constraint** - btree_gist exclusion constraint |
| 036 | Add password_changed_at to users |
| 037 | Add availability timezone support |
| 038 | Add Zoom meeting pending status |
| 039 | Add extend_on_use to pricing options (rolling expiry) |
| 040 | Add session attendance tracking (tutor_joined_at, student_joined_at) |
| 041 | Add video provider preference |
| 042 | Rename notifications metadata to extra_data |
| 043 | Enforce user names (NOT NULL on first_name, last_name) |
| 044 | **Add wallet tables** - wallets, wallet_transactions |
| 045 | Add conversations table |
| 046 | Remove timezone database logic (moved to application) |
| 047 | **Add booking version column** - Optimistic locking |
| 048 | Create webhook_events table |
| 049 | **Add fraud detection** - IP tracking, trial abuse prevention |
| 050 | **Repair missing columns** - Fix columns from duplicate migration numbers |

### Key Migrations (Bolded Above)

These migrations introduce significant schema changes:

1. **Migration 030** - Currency standardization ensures all monetary fields use consistent types and validation.

2. **Migration 033** - Package session consistency prevents data corruption in student credit balances.

3. **Migration 034** - The booking status redesign replaces the old single-status system with four independent fields:
   - `session_state`: REQUESTED, SCHEDULED, ACTIVE, ENDED, CANCELLED, EXPIRED
   - `session_outcome`: COMPLETED, NOT_HELD, NO_SHOW_STUDENT, NO_SHOW_TUTOR
   - `payment_state`: PENDING, AUTHORIZED, CAPTURED, VOIDED, REFUNDED, PARTIALLY_REFUNDED
   - `dispute_state`: NONE, OPEN, RESOLVED_UPHELD, RESOLVED_REFUNDED

4. **Migration 035** - The booking overlap constraint uses PostgreSQL's exclusion constraint feature to prevent double-booking at the database level.

5. **Migration 044** - Wallet tables support the platform's credit system for payments and payouts.

6. **Migration 047** - Optimistic locking prevents race conditions in booking state transitions.

7. **Migration 049** - Fraud detection enables trial abuse prevention by tracking registration patterns.

8. **Migration 050** - Repair migration that adds columns which were missed due to duplicate migration prefix issues.

## Running Migrations

### Automatic (Recommended)

Migrations run automatically when the backend starts:

```bash
make dev        # Starts backend, which applies migrations
# or
docker compose up backend
```

### Manual Application

To apply migrations manually:

```bash
# Connect to database
docker compose exec db psql -U postgres -d authapp

# Run a specific migration
\i /docker-entrypoint-initdb.d/migrations/034_booking_status_redesign.sql
```

### Verify Migrations Applied

```bash
# Check applied migrations
docker compose exec db psql -U postgres -d authapp -c "SELECT * FROM schema_migrations ORDER BY version;"

# Run verification script
./scripts/verify-database.sh
```

## Creating New Migrations

1. **Number**: Use the next available number (check existing files)
2. **Filename**: `{number}_{descriptive_name}.sql`
3. **Idempotency**: Use `IF NOT EXISTS`, `DO $$ ... END $$` blocks
4. **Verification**: Include validation queries at the end
5. **Comments**: Document the purpose and any application code changes needed

### Template

```sql
-- Migration NNN: Short description
-- Purpose: Why this migration exists
-- Date: YYYY-MM-DD

-- ============================================================================
-- STEP 1: Add new columns/tables
-- ============================================================================

ALTER TABLE example ADD COLUMN IF NOT EXISTS new_column VARCHAR(50);

-- ============================================================================
-- STEP 2: Migrate existing data (if needed)
-- ============================================================================

UPDATE example SET new_column = 'default' WHERE new_column IS NULL;

-- ============================================================================
-- STEP 3: Add constraints (after data migration)
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

-- ============================================================================
-- STEP 5: Record migration
-- ============================================================================

INSERT INTO schema_migrations (version, description)
VALUES ('NNN', 'Short description')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration NNN completed successfully';
END $$;
```

## Rollback

Migrations do not have automatic rollback. If you need to undo a migration:

1. Write a new migration that reverses the changes
2. Test thoroughly in a non-production environment
3. For critical issues, restore from backup

## Troubleshooting

### Migration fails with constraint violation

The migration may be trying to add a constraint to existing invalid data. Options:

1. Fix the data first with UPDATE statements
2. Use `EXCEPTION WHEN` blocks to skip problematic constraints
3. Add constraint as `NOT VALID` then validate separately

### Migration runs but column/constraint missing

Check if the migration actually ran:

```sql
SELECT * FROM schema_migrations WHERE version = 'NNN';
```

If recorded but missing, the migration may have partially succeeded. Re-run the specific statement or use migration 050 as a template for repairs.

### Duplicate migration numbers

Historical migrations (006-020) were archived but new migrations accidentally reused some numbers (039-041). Migration 050 repairs columns that were missed due to this overlap.

## Related Documentation

- [SOURCE_OF_TRUTH.md](../SOURCE_OF_TRUTH.md) - Schema integrity documentation
- [init.sql](../init.sql) - Consolidated base schema
- [verify-database.sh](../../scripts/verify-database.sh) - Database verification script
