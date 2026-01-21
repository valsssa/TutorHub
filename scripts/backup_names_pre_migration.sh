#!/bin/bash
# ============================================================================
# EduStream Naming Data Backup Script
# Phase 1.1: Automated backup process for name-related data
# ============================================================================

set -e  # Exit on any error

# Configuration
BACKUP_DIR="./database/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/naming_backup_${TIMESTAMP}.sql"
LOG_FILE="${BACKUP_DIR}/backup_log_${TIMESTAMP}.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

# Error function
error() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Success function
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Info function
info() {
    echo -e "${BLUE}INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Warning function
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if database is accessible
check_db_connection() {
    log "Checking database connection..."
    if ! docker compose exec -T db psql -U postgres -d authapp -c "SELECT 1;" >/dev/null 2>&1; then
        error "Cannot connect to database. Make sure containers are running with: docker compose up -d"
    fi
    success "Database connection verified"
}

# Function to run audit queries
run_audit() {
    log "Running name consistency audit..."

    AUDIT_RESULTS="${BACKUP_DIR}/audit_results_${TIMESTAMP}.txt"

    {
        echo "=== EduStream Naming Consistency Audit ==="
        echo "Timestamp: $(date)"
        echo ""

        echo "=== Name Distribution Across Tables ==="
        docker compose exec -T db psql -U postgres -d authapp -f database/migrations/audit_name_consistency.sql -q | head -20

        echo ""
        echo "=== Data Conflicts Summary ==="
        docker compose exec -T db psql -U postgres -d authapp -c "
        SELECT conflict_type, total_conflicts, first_name_conflicts, last_name_conflicts,
               users_missing_first_name, users_missing_last_name
        FROM (
            SELECT
                'users_vs_user_profiles' as conflict_type,
                COUNT(*) as total_conflicts,
                COUNT(*) FILTER (WHERE u.first_name != up.first_name) as first_name_conflicts,
                COUNT(*) FILTER (WHERE u.last_name != up.last_name) as last_name_conflicts,
                COUNT(*) FILTER (WHERE u.first_name IS NULL AND up.first_name IS NOT NULL) as users_missing_first_name,
                COUNT(*) FILTER (WHERE u.last_name IS NULL AND up.last_name IS NOT NULL) as users_missing_last_name
            FROM users u
            JOIN user_profiles up ON u.id = up.user_id
            WHERE u.is_active = TRUE
                AND (
                    u.first_name != up.first_name
                    OR u.last_name != up.last_name
                    OR (u.first_name IS NULL AND up.first_name IS NOT NULL)
                    OR (u.last_name IS NULL AND up.last_name IS NOT NULL)
                    OR (u.first_name IS NOT NULL AND up.first_name IS NULL)
                    OR (u.last_name IS NOT NULL AND up.last_name IS NULL)
                )
        ) conflicts;"

        echo ""
        echo "=== Users Missing Names by Role ==="
        docker compose exec -T db psql -U postgres -d authapp -c "
        SELECT role, total_users, missing_first_name, missing_last_name, missing_both_names,
               ROUND(missing_both_names::decimal / total_users::decimal * 100, 1) as pct_missing
        FROM (
            SELECT role,
                   COUNT(*) as total_users,
                   COUNT(*) FILTER (WHERE first_name IS NULL) as missing_first_name,
                   COUNT(*) FILTER (WHERE last_name IS NULL) as missing_last_name,
                   COUNT(*) FILTER (WHERE first_name IS NULL AND last_name IS NULL) as missing_both_names
            FROM users
            WHERE is_active = TRUE
            GROUP BY role
        ) stats
        ORDER BY total_users DESC;"

    } > "$AUDIT_RESULTS"

    success "Audit completed. Results saved to: $AUDIT_RESULTS"
}

# Function to create database backup
create_backup() {
    log "Creating comprehensive database backup..."

    # Create a full database dump as additional safety measure
    FULL_BACKUP="${BACKUP_DIR}/full_db_backup_${TIMESTAMP}.sql"
    docker compose exec -T db pg_dump -U postgres authapp > "$FULL_BACKUP"

    if [ $? -eq 0 ]; then
        success "Full database backup created: $FULL_BACKUP"
    else
        error "Failed to create full database backup"
    fi
}

# Function to run naming data backup
run_naming_backup() {
    log "Running naming data backup script..."

    # Execute the backup SQL script
    docker compose exec -T db psql -U postgres -d authapp -f database/migrations/backup_name_data.sql

    if [ $? -eq 0 ]; then
        success "Naming data backup completed successfully"
    else
        error "Naming data backup failed"
    fi
}

# Function to verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    VERIFICATION_RESULTS="${BACKUP_DIR}/verification_${TIMESTAMP}.txt"

    {
        echo "=== Backup Verification Results ==="
        echo "Timestamp: $(date)"
        echo ""

        echo "=== Backup Table Record Counts ==="
        docker compose exec -T db psql -U postgres -d authapp -c "
        SET search_path TO naming_backup, public;
        SELECT 'backup_users_names' as table_name, COUNT(*) as record_count FROM backup_users_names
        UNION ALL
        SELECT 'backup_user_profiles_names', COUNT(*) FROM backup_user_profiles_names
        UNION ALL
        SELECT 'backup_student_profiles_names', COUNT(*) FROM backup_student_profiles_names
        UNION ALL
        SELECT 'backup_bookings_snapshot_names', COUNT(*) FROM backup_bookings_snapshot_names
        UNION ALL
        SELECT 'backup_name_resolution_map', COUNT(*) FROM backup_name_resolution_map;"

        echo ""
        echo "=== Original vs Backup Comparison ==="
        docker compose exec -T db psql -U postgres -d authapp -c "
        WITH original_counts AS (
            SELECT 'users' as source, COUNT(*) as count FROM users WHERE is_active = TRUE AND (first_name IS NOT NULL OR last_name IS NOT NULL)
            UNION ALL
            SELECT 'user_profiles', COUNT(*) FROM user_profiles up JOIN users u ON up.user_id = u.id WHERE u.is_active = TRUE AND (up.first_name IS NOT NULL OR up.last_name IS NOT NULL)
            UNION ALL
            SELECT 'student_profiles', COUNT(*) FROM student_profiles sp JOIN users u ON sp.user_id = u.id WHERE u.is_active = TRUE AND (sp.first_name IS NOT NULL OR sp.last_name IS NOT NULL)
        ),
        backup_counts AS (
            SELECT 'users' as source, COUNT(*) as count FROM naming_backup.backup_users_names
            UNION ALL
            SELECT 'user_profiles', COUNT(*) FROM naming_backup.backup_user_profiles_names
            UNION ALL
            SELECT 'student_profiles', COUNT(*) FROM naming_backup.backup_student_profiles_names
        )
        SELECT oc.source, oc.count as original_count, bc.count as backup_count,
               CASE WHEN oc.count = bc.count THEN 'MATCH' ELSE 'MISMATCH' END as status
        FROM original_counts oc
        JOIN backup_counts bc ON oc.source = bc.source;"

        echo ""
        echo "=== Name Resolution Map Preview ==="
        docker compose exec -T db psql -U postgres -d authapp -c "
        SET search_path TO naming_backup, public;
        SELECT user_id, email, role, winning_source, resolved_first_name, resolved_last_name,
               first_name_impact, last_name_impact, alternative_sources_count
        FROM backup_name_resolution_map
        ORDER BY user_id
        LIMIT 10;"

    } > "$VERIFICATION_RESULTS"

    success "Backup verification completed. Results saved to: $VERIFICATION_RESULTS"
}

# Function to generate backup report
generate_report() {
    log "Generating backup completion report..."

    REPORT_FILE="${BACKUP_DIR}/backup_report_${TIMESTAMP}.md"

    cat > "$REPORT_FILE" << EOF
# EduStream Naming Data Backup Report

**Backup Date:** $(date)
**Backup ID:** ${TIMESTAMP}

## Backup Overview

This backup was created as part of the EduStream naming consistency migration (Phase 1.1).
All name-related data has been preserved before making any schema or data changes.

## Files Created

### Database Backups
- **Full Database Backup:** \`${BACKUP_DIR}/full_db_backup_${TIMESTAMP}.sql\`
- **Naming Data Backup:** Executed via \`database/migrations/backup_name_data.sql\`

### Audit & Verification Files
- **Audit Results:** \`${BACKUP_DIR}/audit_results_${TIMESTAMP}.txt\`
- **Verification Results:** \`${BACKUP_DIR}/verification_${TIMESTAMP}.txt\`
- **Backup Log:** \`${BACKUP_DIR}/backup_log_${TIMESTAMP}.txt\`
- **Backup Report:** \`${REPORT_FILE}\`

## Backup Contents

The following backup tables were created in the \`naming_backup\` schema:

1. **backup_users_names** - Complete snapshot of names in users table
2. **backup_user_profiles_names** - Complete snapshot of names in user_profiles table
3. **backup_student_profiles_names** - Complete snapshot of names in student_profiles table
4. **backup_bookings_snapshot_names** - Snapshot of concatenated names in bookings
5. **backup_name_resolution_map** - Conflict resolution mapping for migration

## Next Steps

After verifying this backup is complete and accurate:

1. **Phase 1.2**: Remove duplicate name fields from profile tables
2. **Phase 1.3**: Migrate profile names to users table using resolution map
3. **Phase 2.1-3.2**: Update application code for single source of truth

## Rollback Instructions

If migration needs to be rolled back:

1. Restore from full database backup: \`full_db_backup_${TIMESTAMP}.sql\`
2. Or restore individual tables from \`naming_backup\` schema
3. Verify data integrity matches this report

## Contact

For questions about this backup, refer to the naming consistency migration documentation.
EOF

    success "Backup report generated: $REPORT_FILE"
}

# Main execution
main() {
    log "Starting EduStream naming data backup process..."
    log "Backup ID: $TIMESTAMP"

    # Pre-flight checks
    check_db_connection

    # Execute backup steps
    run_audit
    create_backup
    run_naming_backup
    verify_backup
    generate_report

    log "EduStream naming data backup process completed successfully!"
    log "Backup ID: $TIMESTAMP"
    log "Backup directory: $BACKUP_DIR"
    log "Review the generated report for complete details."

    # Final success message
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}BACKUP COMPLETED SUCCESSFULLY${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${BLUE}Backup ID:${NC} $TIMESTAMP"
    echo -e "${BLUE}Backup Directory:${NC} $BACKUP_DIR"
    echo -e "${BLUE}Review the backup report for complete verification details${NC}"
    echo -e "${GREEN}================================================================${NC}"
}

# Run main function
main "$@"