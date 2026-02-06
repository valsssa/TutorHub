#!/bin/bash
# =============================================================================
# Database Verification Script
# =============================================================================
# Checks for common database issues:
# 1. NULL monetary values
# 2. Overlapping bookings
# 3. Orphaned records
# 4. Constraint existence
# 5. Index existence
# 6. Migration verification
#
# Usage: ./scripts/verify-database.sh [--fix]
#        --fix: Attempt to fix issues where possible (use with caution)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0
PASSED=0
WARNINGS=0

# Parse arguments
FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
    echo -e "${YELLOW}Running in FIX mode - will attempt to repair issues${NC}"
fi

# Helper functions
print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "[INFO] $1"
}

# Execute SQL and capture result
run_sql() {
    docker compose exec -T db psql -U postgres -d authapp -t -A -c "$1" 2>/dev/null
}

# Check if docker compose is running
check_docker() {
    if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -q "db"; then
        echo -e "${RED}Error: Database container is not running${NC}"
        echo "Start the database with: make dev"
        exit 1
    fi
}

echo "=============================================="
echo "  EduStream Database Verification Script"
echo "=============================================="
echo ""

check_docker

# =============================================================================
# CHECK 1: NULL Monetary Values
# =============================================================================
echo "--- Check 1: Monetary Value Integrity ---"

# Check bookings for NULL monetary fields
NULL_RATE_CENTS=$(run_sql "SELECT COUNT(*) FROM bookings WHERE rate_cents IS NULL AND deleted_at IS NULL;")
if [[ "$NULL_RATE_CENTS" -gt 0 ]]; then
    print_fail "Found $NULL_RATE_CENTS bookings with NULL rate_cents"
else
    print_pass "No NULL rate_cents in bookings"
fi

NULL_PLATFORM_FEE=$(run_sql "SELECT COUNT(*) FROM bookings WHERE platform_fee_cents IS NULL AND deleted_at IS NULL;")
if [[ "$NULL_PLATFORM_FEE" -gt 0 ]]; then
    print_fail "Found $NULL_PLATFORM_FEE bookings with NULL platform_fee_cents"
else
    print_pass "No NULL platform_fee_cents in bookings"
fi

NULL_TUTOR_EARNINGS=$(run_sql "SELECT COUNT(*) FROM bookings WHERE tutor_earnings_cents IS NULL AND deleted_at IS NULL;")
if [[ "$NULL_TUTOR_EARNINGS" -gt 0 ]]; then
    print_fail "Found $NULL_TUTOR_EARNINGS bookings with NULL tutor_earnings_cents"
else
    print_pass "No NULL tutor_earnings_cents in bookings"
fi

# Check for negative monetary values
NEGATIVE_AMOUNTS=$(run_sql "SELECT COUNT(*) FROM bookings WHERE (rate_cents < 0 OR platform_fee_cents < 0 OR tutor_earnings_cents < 0) AND deleted_at IS NULL;")
if [[ "$NEGATIVE_AMOUNTS" -gt 0 ]]; then
    print_fail "Found $NEGATIVE_AMOUNTS bookings with negative monetary values"
else
    print_pass "No negative monetary values in bookings"
fi

# Check wallet balances
NEGATIVE_WALLET=$(run_sql "SELECT COUNT(*) FROM wallets WHERE balance_cents < 0 OR pending_cents < 0;" 2>/dev/null || echo "0")
if [[ "$NEGATIVE_WALLET" -gt 0 ]]; then
    print_fail "Found $NEGATIVE_WALLET wallets with negative balances"
else
    print_pass "No negative wallet balances"
fi

echo ""

# =============================================================================
# CHECK 2: Overlapping Bookings
# =============================================================================
echo "--- Check 2: Booking Overlap Detection ---"

# Check for overlapping bookings (should be prevented by exclusion constraint)
OVERLAPPING=$(run_sql "
SELECT COUNT(*) FROM (
    SELECT b1.id
    FROM bookings b1
    JOIN bookings b2 ON b1.tutor_profile_id = b2.tutor_profile_id
        AND b1.id < b2.id
        AND b1.session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE')
        AND b2.session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE')
        AND b1.deleted_at IS NULL
        AND b2.deleted_at IS NULL
        AND tstzrange(b1.start_time, b1.end_time, '[)') && tstzrange(b2.start_time, b2.end_time, '[)')
) AS overlaps;
")
if [[ "$OVERLAPPING" -gt 0 ]]; then
    print_fail "Found $OVERLAPPING overlapping active bookings"
    if [[ "$FIX_MODE" == true ]]; then
        print_warn "Cannot auto-fix overlapping bookings - manual review required"
    fi
else
    print_pass "No overlapping active bookings"
fi

echo ""

# =============================================================================
# CHECK 3: Orphaned Records
# =============================================================================
echo "--- Check 3: Orphaned Records ---"

# Check for bookings with non-existent tutor profiles
ORPHAN_TUTOR=$(run_sql "
SELECT COUNT(*) FROM bookings b
WHERE b.tutor_profile_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM tutor_profiles tp WHERE tp.id = b.tutor_profile_id)
AND b.deleted_at IS NULL;
")
if [[ "$ORPHAN_TUTOR" -gt 0 ]]; then
    print_warn "Found $ORPHAN_TUTOR bookings referencing non-existent tutor profiles"
else
    print_pass "No orphaned tutor profile references in bookings"
fi

# Check for bookings with non-existent students
ORPHAN_STUDENT=$(run_sql "
SELECT COUNT(*) FROM bookings b
WHERE b.student_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = b.student_id)
AND b.deleted_at IS NULL;
")
if [[ "$ORPHAN_STUDENT" -gt 0 ]]; then
    print_warn "Found $ORPHAN_STUDENT bookings referencing non-existent students"
else
    print_pass "No orphaned student references in bookings"
fi

# Check for student packages with non-existent pricing options
ORPHAN_PRICING=$(run_sql "
SELECT COUNT(*) FROM student_packages sp
WHERE NOT EXISTS (SELECT 1 FROM tutor_pricing_options tpo WHERE tpo.id = sp.pricing_option_id);
" 2>/dev/null || echo "0")
if [[ "$ORPHAN_PRICING" -gt 0 ]]; then
    print_fail "Found $ORPHAN_PRICING student packages referencing non-existent pricing options"
else
    print_pass "No orphaned pricing option references"
fi

echo ""

# =============================================================================
# CHECK 4: Constraint Existence
# =============================================================================
echo "--- Check 4: Required Constraints ---"

# Check booking state constraints
BOOKING_STATE_CONSTRAINT=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname = 'valid_session_state' AND conrelid = 'bookings'::regclass;
")
if [[ "$BOOKING_STATE_CONSTRAINT" -eq 0 ]]; then
    print_fail "Missing valid_session_state constraint on bookings"
else
    print_pass "valid_session_state constraint exists"
fi

PAYMENT_STATE_CONSTRAINT=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname = 'valid_payment_state' AND conrelid = 'bookings'::regclass;
")
if [[ "$PAYMENT_STATE_CONSTRAINT" -eq 0 ]]; then
    print_fail "Missing valid_payment_state constraint on bookings"
else
    print_pass "valid_payment_state constraint exists"
fi

DISPUTE_STATE_CONSTRAINT=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname = 'valid_dispute_state' AND conrelid = 'bookings'::regclass;
")
if [[ "$DISPUTE_STATE_CONSTRAINT" -eq 0 ]]; then
    print_fail "Missing valid_dispute_state constraint on bookings"
else
    print_pass "valid_dispute_state constraint exists"
fi

# Check package consistency constraint
PACKAGE_CONSISTENCY=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname = 'chk_sessions_consistency' AND conrelid = 'student_packages'::regclass;
" 2>/dev/null || echo "0")
if [[ "$PACKAGE_CONSISTENCY" -eq 0 ]]; then
    print_warn "Missing chk_sessions_consistency constraint on student_packages"
else
    print_pass "Package sessions consistency constraint exists"
fi

# Check booking overlap exclusion constraint
OVERLAP_CONSTRAINT=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname = 'bookings_no_time_overlap' AND contype = 'x';
")
if [[ "$OVERLAP_CONSTRAINT" -eq 0 ]]; then
    print_fail "Missing bookings_no_time_overlap exclusion constraint"
else
    print_pass "Booking overlap exclusion constraint exists"
fi

# Check currency format constraints
CURRENCY_CONSTRAINT=$(run_sql "
SELECT COUNT(*) FROM pg_constraint
WHERE conname LIKE '%valid_currency%' OR conname LIKE '%currency_format%';
")
if [[ "$CURRENCY_CONSTRAINT" -lt 4 ]]; then
    print_warn "Some currency format constraints may be missing (found: $CURRENCY_CONSTRAINT)"
else
    print_pass "Currency format constraints exist"
fi

echo ""

# =============================================================================
# CHECK 5: Index Existence
# =============================================================================
echo "--- Check 5: Performance Indexes ---"

# Check critical indexes
check_index() {
    local index_name=$1
    local exists=$(run_sql "SELECT COUNT(*) FROM pg_indexes WHERE indexname = '$index_name';")
    if [[ "$exists" -eq 0 ]]; then
        print_warn "Missing index: $index_name"
    else
        print_pass "Index exists: $index_name"
    fi
}

check_index "idx_bookings_session_state_times"
check_index "idx_bookings_requested_created"
check_index "idx_bookings_payment_state"
check_index "idx_messages_conversation"
check_index "idx_messages_unread"
check_index "idx_student_packages_active_lookup"

echo ""

# =============================================================================
# CHECK 6: Migration Verification
# =============================================================================
echo "--- Check 6: Migration Status ---"

# Check if schema_migrations table exists
MIGRATION_TABLE=$(run_sql "
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name = 'schema_migrations';
")

if [[ "$MIGRATION_TABLE" -eq 0 ]]; then
    print_warn "schema_migrations table does not exist - cannot verify migrations"
else
    # Count applied migrations
    MIGRATION_COUNT=$(run_sql "SELECT COUNT(*) FROM schema_migrations;")
    print_info "Applied migrations: $MIGRATION_COUNT"

    # Check for specific critical migrations
    M034=$(run_sql "SELECT COUNT(*) FROM schema_migrations WHERE version = '034';")
    if [[ "$M034" -eq 0 ]]; then
        print_warn "Migration 034 (booking status redesign) may not be applied"
    else
        print_pass "Migration 034 (booking status redesign) applied"
    fi

    M035=$(run_sql "SELECT COUNT(*) FROM schema_migrations WHERE version = '035';")
    if [[ "$M035" -eq 0 ]]; then
        print_warn "Migration 035 (booking overlap constraint) may not be applied"
    else
        print_pass "Migration 035 (booking overlap constraint) applied"
    fi
fi

echo ""

# =============================================================================
# CHECK 7: Package Session Consistency
# =============================================================================
echo "--- Check 7: Package Session Consistency ---"

INCONSISTENT_PACKAGES=$(run_sql "
SELECT COUNT(*) FROM student_packages
WHERE sessions_remaining != sessions_purchased - sessions_used;
" 2>/dev/null || echo "0")

if [[ "$INCONSISTENT_PACKAGES" -gt 0 ]]; then
    print_fail "Found $INCONSISTENT_PACKAGES packages with inconsistent session counts"
    if [[ "$FIX_MODE" == true ]]; then
        print_info "Attempting to fix inconsistent packages..."
        run_sql "
        UPDATE student_packages
        SET sessions_remaining = sessions_purchased - sessions_used
        WHERE sessions_remaining != sessions_purchased - sessions_used;
        "
        print_pass "Fixed inconsistent packages"
    fi
else
    print_pass "All package session counts are consistent"
fi

echo ""

# =============================================================================
# CHECK 8: Required Extensions
# =============================================================================
echo "--- Check 8: PostgreSQL Extensions ---"

BTREE_GIST=$(run_sql "SELECT COUNT(*) FROM pg_extension WHERE extname = 'btree_gist';")
if [[ "$BTREE_GIST" -eq 0 ]]; then
    print_fail "Missing btree_gist extension (required for overlap constraint)"
else
    print_pass "btree_gist extension installed"
fi

UUID_OSSP=$(run_sql "SELECT COUNT(*) FROM pg_extension WHERE extname = 'uuid-ossp';")
if [[ "$UUID_OSSP" -eq 0 ]]; then
    print_warn "uuid-ossp extension not installed"
else
    print_pass "uuid-ossp extension installed"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo "=============================================="
echo "  Verification Summary"
echo "=============================================="
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Database verification FAILED${NC}"
    echo "Please review the failed checks above and fix the issues."
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}Database verification passed with warnings${NC}"
    exit 0
else
    echo -e "${GREEN}Database verification PASSED${NC}"
    exit 0
fi
