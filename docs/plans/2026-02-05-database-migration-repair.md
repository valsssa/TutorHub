# Database Migration Repair Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix broken migration system by renumbering duplicates, updating init.sql, and creating a repair migration.

**Architecture:** Three-pronged fix: (1) Update init.sql to include all missing columns for fresh installs, (2) Renumber duplicate migrations to unique version numbers, (3) Create repair migration that safely adds missing columns to existing databases.

**Tech Stack:** PostgreSQL, SQL migrations, Docker

---

## Problem Summary

| Issue | Details |
|-------|---------|
| Duplicate prefixes | 028 (2 files), 035 (3 files), 039 (2 files) |
| Missing columns | Migrations 039-041 columns not in init.sql or DB |
| Broken state | Migrations marked applied but columns missing |

## Missing Columns to Add

**From migration 039 (extend_on_use):**
- `tutor_pricing_options.extend_on_use` BOOLEAN DEFAULT FALSE NOT NULL
- `student_packages.expiry_warning_sent` BOOLEAN DEFAULT FALSE NOT NULL

**From migration 040 (attendance tracking):**
- `bookings.tutor_joined_at` TIMESTAMPTZ
- `bookings.student_joined_at` TIMESTAMPTZ

**From migration 041 (video provider):**
- `tutor_profiles.preferred_video_provider` VARCHAR(20) DEFAULT 'zoom'
- `tutor_profiles.custom_meeting_url_template` VARCHAR(500)
- `tutor_profiles.video_provider_configured` BOOLEAN DEFAULT FALSE
- `bookings.video_provider` VARCHAR(20)
- `bookings.google_meet_link` VARCHAR(500)

---

### Task 1: Renumber Duplicate Migration 028_remove_timezone_db_logic

**Files:**
- Rename: `database/migrations/028_remove_timezone_db_logic.sql` → `database/migrations/046_remove_timezone_db_logic.sql`

**Step 1: Rename the file**

```bash
mv database/migrations/028_remove_timezone_db_logic.sql database/migrations/046_remove_timezone_db_logic.sql
```

**Step 2: Verify rename**

```bash
ls database/migrations/028*.sql database/migrations/046*.sql
```

Expected: Only `028_create_student_notes.sql` and new `046_remove_timezone_db_logic.sql`

---

### Task 2: Renumber Duplicate Migration 035_add_booking_version_column

**Files:**
- Rename: `database/migrations/035_add_booking_version_column.sql` → `database/migrations/047_add_booking_version_column.sql`

**Step 1: Rename the file**

```bash
mv database/migrations/035_add_booking_version_column.sql database/migrations/047_add_booking_version_column.sql
```

**Step 2: Verify rename**

```bash
ls database/migrations/035*.sql database/migrations/047*.sql
```

---

### Task 3: Renumber Duplicate Migration 035_create_webhook_events

**Files:**
- Rename: `database/migrations/035_create_webhook_events.sql` → `database/migrations/048_create_webhook_events.sql`

**Step 1: Rename the file**

```bash
mv database/migrations/035_create_webhook_events.sql database/migrations/048_create_webhook_events.sql
```

**Step 2: Verify rename**

```bash
ls database/migrations/035*.sql database/migrations/048*.sql
```

Expected: Only `035_add_booking_overlap_constraint.sql` remains with prefix 035

---

### Task 4: Renumber Duplicate Migration 039_add_fraud_detection

**Files:**
- Rename: `database/migrations/039_add_fraud_detection.sql` → `database/migrations/049_add_fraud_detection.sql`

**Step 1: Rename the file**

```bash
mv database/migrations/039_add_fraud_detection.sql database/migrations/049_add_fraud_detection.sql
```

**Step 2: Verify no more duplicates**

```bash
ls database/migrations/ | cut -d'_' -f1 | sort | uniq -d
```

Expected: Empty output (no duplicates)

---

### Task 5: Create Repair Migration 050

**Files:**
- Create: `database/migrations/050_repair_missing_columns.sql`

**Step 1: Create the repair migration**

Create file `database/migrations/050_repair_missing_columns.sql`:

```sql
-- Migration 050: Repair missing columns from migrations 039-041
-- Purpose: Add columns that were skipped due to duplicate migration prefixes
-- Date: 2026-02-05
--
-- This migration safely adds all columns that may be missing in existing databases.
-- Uses IF NOT EXISTS / DO $$ blocks to be idempotent.

-- =============================================================================
-- FROM MIGRATION 039: extend_on_use for pricing options
-- =============================================================================

ALTER TABLE tutor_pricing_options
ADD COLUMN IF NOT EXISTS extend_on_use BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN tutor_pricing_options.extend_on_use IS
    'When TRUE, package expiration extends by validity_days on each credit use (rolling expiry)';

ALTER TABLE student_packages
ADD COLUMN IF NOT EXISTS expiry_warning_sent BOOLEAN DEFAULT FALSE NOT NULL;

COMMENT ON COLUMN student_packages.expiry_warning_sent IS
    'Whether an expiration warning notification has been sent for this package';

-- =============================================================================
-- FROM MIGRATION 040: Session attendance tracking
-- =============================================================================

ALTER TABLE bookings ADD COLUMN IF NOT EXISTS tutor_joined_at TIMESTAMPTZ;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS student_joined_at TIMESTAMPTZ;

COMMENT ON COLUMN bookings.tutor_joined_at IS 'Timestamp when tutor clicked join/entered the session';
COMMENT ON COLUMN bookings.student_joined_at IS 'Timestamp when student clicked join/entered the session';

CREATE INDEX IF NOT EXISTS idx_bookings_attendance_check
    ON bookings(session_state, tutor_joined_at, student_joined_at)
    WHERE session_state = 'ACTIVE';

-- =============================================================================
-- FROM MIGRATION 041: Video provider preference
-- =============================================================================

-- Tutor profiles video provider fields
ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS preferred_video_provider VARCHAR(20) DEFAULT 'zoom';

ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS custom_meeting_url_template VARCHAR(500);

ALTER TABLE tutor_profiles
    ADD COLUMN IF NOT EXISTS video_provider_configured BOOLEAN DEFAULT FALSE;

-- Add constraint for valid provider values (drop first to avoid duplicate)
ALTER TABLE tutor_profiles DROP CONSTRAINT IF EXISTS valid_video_provider;

ALTER TABLE tutor_profiles
    ADD CONSTRAINT valid_video_provider CHECK (
        preferred_video_provider IN ('zoom', 'google_meet', 'teams', 'custom', 'manual')
    );

COMMENT ON COLUMN tutor_profiles.preferred_video_provider IS
    'Preferred video provider: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN tutor_profiles.custom_meeting_url_template IS
    'Custom meeting URL template for Teams/custom providers. Supports placeholders: {booking_id}';
COMMENT ON COLUMN tutor_profiles.video_provider_configured IS
    'Whether the video provider is properly configured and ready to use';

-- Bookings video provider fields
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS video_provider VARCHAR(20);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS google_meet_link VARCHAR(500);

COMMENT ON COLUMN bookings.video_provider IS
    'Video provider used for this booking: zoom, google_meet, teams, custom, manual';
COMMENT ON COLUMN bookings.google_meet_link IS
    'Google Meet link if using Google Meet as provider';

-- =============================================================================
-- Verification
-- =============================================================================

DO $$
DECLARE
    missing_cols TEXT := '';
BEGIN
    -- Check tutor_profiles columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='tutor_profiles' AND column_name='preferred_video_provider') THEN
        missing_cols := missing_cols || 'tutor_profiles.preferred_video_provider, ';
    END IF;

    -- Check bookings columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='bookings' AND column_name='tutor_joined_at') THEN
        missing_cols := missing_cols || 'bookings.tutor_joined_at, ';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='bookings' AND column_name='video_provider') THEN
        missing_cols := missing_cols || 'bookings.video_provider, ';
    END IF;

    -- Check tutor_pricing_options columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='tutor_pricing_options' AND column_name='extend_on_use') THEN
        missing_cols := missing_cols || 'tutor_pricing_options.extend_on_use, ';
    END IF;

    IF missing_cols != '' THEN
        RAISE EXCEPTION 'Migration 050 failed - missing columns: %', missing_cols;
    END IF;

    RAISE NOTICE 'Migration 050 completed successfully: All missing columns added';
END $$;
```

**Step 2: Verify file created**

```bash
cat database/migrations/050_repair_missing_columns.sql | head -20
```

---

### Task 6: Update init.sql - Add Missing tutor_profiles Columns

**Files:**
- Modify: `database/init.sql` (around line 109-154, tutor_profiles table)

**Step 1: Add video provider columns to tutor_profiles table**

Find the `tutor_profiles` CREATE TABLE statement and add these columns after `version INTEGER NOT NULL DEFAULT 1,`:

```sql
    -- Video provider preference (migration 041)
    preferred_video_provider VARCHAR(20) DEFAULT 'zoom',
    custom_meeting_url_template VARCHAR(500),
    video_provider_configured BOOLEAN DEFAULT FALSE,
```

Also add constraint after `CONSTRAINT valid_pricing_model`:

```sql
    CONSTRAINT valid_video_provider CHECK (preferred_video_provider IN ('zoom', 'google_meet', 'teams', 'custom', 'manual'))
```

**Step 2: Verify the edit**

```bash
grep -n "preferred_video_provider" database/init.sql
```

Expected: Line in tutor_profiles table definition

---

### Task 7: Update init.sql - Add Missing bookings Columns

**Files:**
- Modify: `database/init.sql` (around line 349-427, bookings table)

**Step 1: Add attendance and video columns to bookings table**

Find the `bookings` CREATE TABLE and add after `updated_at TIMESTAMPTZ`:

```sql
    -- Session attendance tracking (migration 040)
    tutor_joined_at TIMESTAMPTZ,
    student_joined_at TIMESTAMPTZ,
    -- Video provider tracking (migration 041)
    video_provider VARCHAR(20),
    google_meet_link VARCHAR(500),
```

**Step 2: Add attendance index after other bookings indexes**

```sql
CREATE INDEX IF NOT EXISTS idx_bookings_attendance_check
    ON bookings(session_state, tutor_joined_at, student_joined_at)
    WHERE session_state = 'ACTIVE';
```

**Step 3: Verify the edit**

```bash
grep -n "tutor_joined_at\|video_provider" database/init.sql
```

---

### Task 8: Update init.sql - Add Missing tutor_pricing_options Column

**Files:**
- Modify: `database/init.sql` (around line 256-276, tutor_pricing_options table)

**Step 1: Add extend_on_use column**

Find `tutor_pricing_options` CREATE TABLE and add after `sort_order INTEGER`:

```sql
    -- Rolling expiry behavior (migration 039)
    extend_on_use BOOLEAN DEFAULT FALSE NOT NULL,
```

**Step 2: Verify the edit**

```bash
grep -n "extend_on_use" database/init.sql
```

---

### Task 9: Update init.sql - Add Missing student_packages Column

**Files:**
- Modify: `database/init.sql` (around line 321-343, student_packages table)

**Step 1: Add expiry_warning_sent column**

Find `student_packages` CREATE TABLE and add after `updated_at TIMESTAMPTZ`:

```sql
    -- Expiry notification tracking (migration 039)
    expiry_warning_sent BOOLEAN DEFAULT FALSE NOT NULL,
```

**Step 2: Verify the edit**

```bash
grep -n "expiry_warning_sent" database/init.sql
```

---

### Task 10: Restart Backend and Verify Fix

**Step 1: Restart the backend container to apply migrations**

```bash
docker compose restart backend
```

**Step 2: Wait for startup and check logs**

```bash
sleep 10 && docker compose logs backend --tail=50 2>&1 | grep -E "(Migration|ERROR|startup)"
```

Expected: No migration errors, "Application startup complete"

**Step 3: Verify columns exist**

```bash
docker compose exec -T db psql -U postgres -d authapp -c "
SELECT
    'tutor_profiles.preferred_video_provider' as col,
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='tutor_profiles' AND column_name='preferred_video_provider') as exists
UNION ALL SELECT 'bookings.tutor_joined_at', EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='bookings' AND column_name='tutor_joined_at')
UNION ALL SELECT 'bookings.video_provider', EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='bookings' AND column_name='video_provider')
UNION ALL SELECT 'tutor_pricing_options.extend_on_use', EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='tutor_pricing_options' AND column_name='extend_on_use')
;"
```

Expected: All rows show `t` (true)

---

### Task 11: Commit Changes

**Step 1: Stage all changes**

```bash
git add database/migrations/*.sql database/init.sql
```

**Step 2: Commit**

```bash
git commit -m "fix(db): repair migration system - renumber duplicates and add missing columns

- Renumber duplicate migrations to unique version numbers:
  - 028_remove_timezone_db_logic.sql → 046
  - 035_add_booking_version_column.sql → 047
  - 035_create_webhook_events.sql → 048
  - 039_add_fraud_detection.sql → 049
- Create repair migration 050 to add missing columns safely
- Update init.sql with all missing columns from migrations 039-041:
  - tutor_profiles: video provider preference fields
  - bookings: attendance tracking and video provider fields
  - tutor_pricing_options: extend_on_use
  - student_packages: expiry_warning_sent

Fixes database startup errors caused by duplicate migration prefixes.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks:

- [ ] No duplicate migration prefixes (028, 035, 039 each have only one file)
- [ ] Backend starts without migration errors
- [ ] All missing columns exist in database
- [ ] init.sql contains all columns for fresh installs
- [ ] Changes committed to git
