#!/bin/bash
# Architecture Verification Script
# Checks clean architecture compliance for the backend
#
# Usage: ./backend/scripts/verify-architecture.sh
#        ./backend/scripts/verify-architecture.sh --verbose
#
# Exit codes:
#   0 - All checks passed (clean architecture)
#   1 - Violations found

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

VERBOSE=false
if [[ "${1:-}" == "--verbose" ]] || [[ "${1:-}" == "-v" ]]; then
    VERBOSE=true
fi

TOTAL_VIOLATIONS=0
CHECK_VIOLATIONS=0

# Print header
print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  Clean Architecture Verification${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# Print section header
print_section() {
    echo ""
    echo -e "${YELLOW}----------------------------------------------------------------${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}----------------------------------------------------------------${NC}"
}

# Print violation
print_violation() {
    echo -e "${RED}    [VIOLATION] $1${NC}"
}

# Print success
print_success() {
    echo -e "${GREEN}  [PASS] $1${NC}"
}

# Print check result
print_check_result() {
    local description="$1"
    local count="$2"

    if [[ $count -eq 0 ]]; then
        print_success "$description"
    else
        echo -e "${RED}  [FAIL] $description - $count violation(s)${NC}"
    fi
}

# Check for violations in all domain layers
# Args: $1 = pattern, $2 = description
check_domain_violations() {
    local pattern="$1"
    local description="$2"
    local violations=0
    local results=""

    # Search across all domain directories at once
    if results=$(grep -rn "$pattern" "$BACKEND_DIR/modules/"*/domain/ 2>/dev/null | grep -v "__pycache__" || true); then
        if [[ -n "$results" ]]; then
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    violations=$((violations + 1))
                    CHECK_VIOLATIONS=$((CHECK_VIOLATIONS + 1))
                    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + 1))
                    # Make path relative to repo root for cleaner output
                    local relative_path="${line#$REPO_ROOT/}"
                    print_violation "$relative_path"
                fi
            done <<< "$results"
        fi
    fi

    return 0
}

# Check external services are only in adapters
# Args: $1 = pattern, $2 = service_name
check_external_services() {
    local pattern="$1"
    local service_name="$2"
    local violations=0
    local results=""

    # Search for imports but exclude adapters/, tests, and __pycache__
    if results=$(grep -rn --include="*.py" "$pattern" "$BACKEND_DIR" 2>/dev/null | \
                 grep -v "/adapters/" | \
                 grep -v "/tests/" | \
                 grep -v "test_" | \
                 grep -v "__pycache__" | \
                 grep -v "conftest.py" || true); then
        if [[ -n "$results" ]]; then
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    violations=$((violations + 1))
                    CHECK_VIOLATIONS=$((CHECK_VIOLATIONS + 1))
                    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + 1))
                    local relative_path="${line#$REPO_ROOT/}"
                    print_violation "$relative_path"
                fi
            done <<< "$results"
        fi
    fi

    return 0
}

# Main execution
main() {
    print_header

    # Verify backend directory exists
    if [[ ! -d "$BACKEND_DIR/modules" ]]; then
        echo -e "${RED}Error: Backend modules directory not found at $BACKEND_DIR/modules${NC}"
        exit 1
    fi

    # Check if any domain directories exist
    domain_count=$(find "$BACKEND_DIR/modules" -type d -name "domain" 2>/dev/null | wc -l || echo "0")
    if [[ "$domain_count" -eq 0 ]]; then
        echo -e "${YELLOW}Warning: No domain directories found in modules${NC}"
        echo "Clean architecture verification skipped."
        exit 0
    fi

    echo "  Checking $domain_count domain layer(s) in modules/"
    echo ""

    # ================================================================
    # CHECK 1: No SQLAlchemy in domain layers
    # ================================================================
    print_section "Check 1: No SQLAlchemy in Domain Layers"
    echo "  Domain layers should not depend on ORM implementation details."
    echo ""

    CHECK_VIOLATIONS=0
    check_domain_violations "from sqlalchemy" "SQLAlchemy"
    check_domain_violations "import sqlalchemy" "SQLAlchemy"
    print_check_result "No SQLAlchemy imports in domain/" "$CHECK_VIOLATIONS"

    # ================================================================
    # CHECK 2: No FastAPI in domain layers
    # ================================================================
    print_section "Check 2: No FastAPI in Domain Layers"
    echo "  Domain layers should not depend on web framework details."
    echo ""

    CHECK_VIOLATIONS=0
    check_domain_violations "from fastapi" "FastAPI"
    check_domain_violations "import fastapi" "FastAPI"
    print_check_result "No FastAPI imports in domain/" "$CHECK_VIOLATIONS"

    # ================================================================
    # CHECK 3: No ORM models imports in domain layers
    # ================================================================
    print_section "Check 3: No ORM Models in Domain Layers"
    echo "  Domain layers should use domain entities, not ORM models."
    echo ""

    CHECK_VIOLATIONS=0
    check_domain_violations "from models" "ORM models"
    check_domain_violations "from backend.models" "ORM models"
    print_check_result "No ORM model imports in domain/" "$CHECK_VIOLATIONS"

    # ================================================================
    # CHECK 4: External services only via adapters
    # ================================================================
    print_section "Check 4: External Services Only via Adapters"
    echo "  External service SDKs should only be imported in adapters/."
    echo ""

    CHECK_VIOLATIONS=0

    # Stripe
    check_external_services "^from stripe" "Stripe"
    check_external_services "^import stripe" "Stripe"

    # Brevo (sib_api_v3_sdk)
    check_external_services "^from sib_api_v3_sdk" "Brevo"
    check_external_services "^import sib_api_v3_sdk" "Brevo"

    # boto3 (MinIO/S3)
    check_external_services "^from boto3" "boto3"
    check_external_services "^import boto3" "boto3"

    # Redis
    check_external_services "^from redis" "Redis"
    check_external_services "^import redis" "Redis"

    # Google APIs
    check_external_services "^from google\\." "Google APIs"
    check_external_services "^import google\\." "Google APIs"

    # googleapiclient
    check_external_services "^from googleapiclient" "googleapiclient"
    check_external_services "^import googleapiclient" "googleapiclient"

    print_check_result "External services only in adapters/" "$CHECK_VIOLATIONS"

    # ================================================================
    # SUMMARY
    # ================================================================
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  Summary${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""

    if [[ $TOTAL_VIOLATIONS -eq 0 ]]; then
        echo -e "${GREEN}  All architecture checks passed!${NC}"
        echo -e "${GREEN}  Clean architecture compliance verified.${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}  Found $TOTAL_VIOLATIONS architecture violation(s)${NC}"
        echo ""
        echo "  To fix violations:"
        echo "    1. Move ORM/framework code out of domain layers"
        echo "    2. Use dependency injection and interfaces"
        echo "    3. External services should be accessed via adapters/"
        echo ""
        echo "  For CI integration, this script exits with code 1 on violations."
        echo ""
        exit 1
    fi
}

# Run main function
main "$@"
