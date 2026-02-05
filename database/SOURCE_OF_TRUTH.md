# Database Source of Truth

This directory now contains only **one living schema** and a few **reference copies**. The intent of this document is to highlight the duplicates that already exist under `database/` and to point every maintainer to `database/init.sql` (and `database/migrations/`) as the single, authoritative source.

## Canonical assets

- `database/init.sql` – the consolidated, up‑to‑date schema. All new columns, constraints, indexes, seeding blocks, and trigger definitions belong here.
- `database/migrations/` – the migrations that the backend executes as part of startup. These files are the only scripts that should be modified or added when evolving the schema.

## Duplicate/archival copies

1. `database/init.sql.backup.20251014_131325`
   - A historical snapshot of `init.sql` from November 2025. It contains many of the same table/index definitions plus legacy triggers and business logic that were subsequently moved into the application.
   - **Action**: Keep this file for reference but **do not** edit it; all live schema work happens in `database/init.sql`.

2. `database/migrations_archive/`
   - Contains earlier migration versions (`001`–`020`) that were captured for auditing purposes. Their SQL is duplicated by the active migration pipeline only when a rebuild of a production database is required.
   - **Action**: Use this folder only for historical comparison. New migrations belong in `database/migrations/`.

## Enforcement

- When reviewing or documenting schema changes, refer only to `database/init.sql` and the files in `database/migrations/`.
- Remove any future duplicates by migrating them back into these paths and updating this document if new archival copies are created.

---

## Schema Integrity Features (as of 2026-02)

This section documents key database-level protections and consistency measures.

### Constraints

#### Monetary Value Constraints
All monetary fields use CHECK constraints to prevent negative values and ensure data integrity:

| Table | Column | Constraint |
|-------|--------|------------|
| `bookings` | `hourly_rate` | `CHECK (hourly_rate > 0)` |
| `bookings` | `total_amount` | `CHECK (total_amount >= 0)` |
| `bookings` | `rate_cents` | `CHECK (rate_cents >= 0)` |
| `bookings` | `platform_fee_cents` | `CHECK (platform_fee_cents >= 0)` |
| `bookings` | `tutor_earnings_cents` | `CHECK (tutor_earnings_cents >= 0)` |
| `wallets` | `balance_cents` | `CHECK (balance_cents >= 0)` |
| `wallets` | `pending_cents` | `CHECK (pending_cents >= 0)` |
| `payments` | `amount_cents` | `CHECK (amount_cents > 0)` |
| `student_packages` | `purchase_price` | `CHECK (purchase_price > 0)` |
| `tutor_pricing_options` | `price` | `CHECK (price > 0)` |
| `tutor_profiles` | `hourly_rate` | `CHECK (hourly_rate > 0)` |

#### Booking Overlap Prevention
The `bookings` table has an exclusion constraint using the `btree_gist` extension to prevent double-booking:

```sql
ALTER TABLE bookings
ADD CONSTRAINT bookings_no_time_overlap
EXCLUDE USING gist (
    tutor_profile_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE'));
```

This constraint guarantees no overlapping time ranges for the same tutor in active booking states.

#### Session State Constraints (Migration 034)
The booking system uses a four-field status model with CHECK constraints:

- `session_state`: `CHECK (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED', 'EXPIRED'))`
- `session_outcome`: `CHECK (session_outcome IS NULL OR session_outcome IN ('COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR'))`
- `payment_state`: `CHECK (payment_state IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'REFUNDED', 'PARTIALLY_REFUNDED'))`
- `dispute_state`: `CHECK (dispute_state IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED'))`

#### Package Session Consistency (Migration 033)
```sql
ALTER TABLE student_packages
ADD CONSTRAINT chk_sessions_consistency
CHECK (sessions_remaining = sessions_purchased - sessions_used);
```

#### Foreign Key Cascades
Key cascade behaviors:
- `users.id` referenced by profiles: `ON DELETE CASCADE`
- `tutor_profiles.id` referenced by bookings: `ON DELETE SET NULL` (preserves booking history)
- `wallets.id` referenced by transactions: `ON DELETE RESTRICT` (prevents data loss)
- `student_packages.pricing_option_id`: `ON DELETE RESTRICT` (preserves package integrity)

### Currency Type Standardization (Migration 030)

All currency fields are standardized to:
- Type: `VARCHAR(3)` (previously some were `CHAR(3)`)
- Default: `'USD'`
- Validation: `CHECK (currency ~ '^[A-Z]{3}$')` (ISO 4217 format)

Tables with standardized currency fields:
- `bookings.currency`
- `payments.currency`
- `payouts.currency`
- `refunds.currency`
- `users.currency`
- `tutor_profiles.currency`
- `wallets.currency`
- `wallet_transactions.currency`

### Performance Indexes

Key composite indexes for query optimization (Migration 031):

| Index | Purpose |
|-------|---------|
| `idx_messages_conversation` | Conversation history queries |
| `idx_messages_unread` | Unread message counts |
| `idx_bookings_date_range` | Date range booking queries |
| `idx_bookings_session_state_times` | Auto-transition job queries |
| `idx_bookings_requested_created` | Expired request detection |
| `idx_bookings_disputes_open` | Admin dispute dashboard |
| `idx_bookings_payment_state` | Payment reconciliation |
| `idx_student_packages_active_lookup` | Active package lookup |
| `idx_tutor_profiles_pending_review` | Admin approval queue |

### Soft Delete Consistency

Tables with `deleted_at` column for soft delete:
- `users`
- `tutor_profiles`
- `student_profiles`
- `bookings`
- `messages`

Partial indexes exclude soft-deleted records where appropriate (e.g., `WHERE deleted_at IS NULL`).

### Optimistic Locking (Migration 047)

The `bookings` table includes a `version` column for optimistic locking:
```sql
ALTER TABLE bookings ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
```

This prevents race conditions in booking state transitions by detecting concurrent modifications.

---

## Verification

Run the database verification script to check schema integrity:

```bash
./scripts/verify-database.sh
```

See `database/migrations/README.md` for migration documentation.

