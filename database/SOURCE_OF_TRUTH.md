# Database Source of Truth

**Single source of truth: `database/migrations/`**

All schema definitions live in the migrations directory. There is no separate `init.sql` file.

## Canonical Assets

- `database/migrations/001_baseline_schema.sql` - Complete consolidated schema (tables, indexes, constraints, views, seed data)
- `database/migrations/002_*.sql`, `003_*.sql`, etc. - Future incremental migrations

## How It Works

**Fresh databases:**
1. PostgreSQL runs `001_baseline_schema.sql` via docker-entrypoint-initdb.d
2. Backend startup verifies `schema_migrations` table and records version `001`
3. Any future migrations (`002_*`, `003_*`) are applied automatically

**Existing databases:**
- Backend compares `schema_migrations` table against files in `migrations/`
- Runs any unapplied migrations in order

## Migration Naming Convention

```
migrations/
├── 001_baseline_schema.sql      # Consolidated baseline (from original 001-056)
├── 002_add_feature_x.sql        # Future migration
├── 003_fix_something.sql        # Future migration
└── README.md                    # Migration documentation
```

## Archived Migrations

The `migrations_archive/` directory contains the original 39 migration files (001-056) that were consolidated into the baseline. These are kept for historical reference only and are never executed.

---

## Schema Integrity Features

### Constraints

#### Monetary Value Constraints
All monetary fields use CHECK constraints:

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
The `bookings` table has an exclusion constraint using `btree_gist`:

```sql
ALTER TABLE bookings
ADD CONSTRAINT bookings_no_time_overlap
EXCLUDE USING gist (
    tutor_profile_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE'));
```

#### Session State Constraints
Four-field status model with CHECK constraints:

- `session_state`: `CHECK (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED', 'EXPIRED'))`
- `session_outcome`: `CHECK (session_outcome IS NULL OR session_outcome IN ('COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR'))`
- `payment_state`: `CHECK (payment_state IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'REFUNDED', 'PARTIALLY_REFUNDED'))`
- `dispute_state`: `CHECK (dispute_state IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED'))`

### Currency Type Standardization

All currency fields:
- Type: `VARCHAR(3)`
- Default: `'USD'`
- Validation: `CHECK (currency ~ '^[A-Z]{3}$')` (ISO 4217 format)

### Soft Delete Consistency

Tables with `deleted_at` column:
- `users`, `tutor_profiles`, `student_profiles`, `bookings`, `messages`, `notifications`, `wallets`, etc.

Partial indexes exclude soft-deleted records: `WHERE deleted_at IS NULL`

### Optimistic Locking

The `bookings` table includes a `version` column for preventing race conditions.

---

## Verification

Run the database verification script:

```bash
./scripts/verify-database.sh
```

---

## Change History

- **2026-02-06**: Consolidated 39 migrations into single `001_baseline_schema.sql`. Deleted `init.sql`.
- **2026-02-05**: Migration 056 - Comprehensive database fixes (47 issues)
