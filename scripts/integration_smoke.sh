#!/bin/bash
# Integration Smoke Test - EduStream Frontend ↔ Backend
#
# This script verifies that the frontend can successfully communicate
# with the backend API. It tests critical endpoints and reports results.
#
# Usage:
#   ./scripts/integration_smoke.sh                    # Use defaults
#   ./scripts/integration_smoke.sh http://localhost:8000  # Custom backend URL
#   BACKEND_URL=http://localhost:8000 ./scripts/integration_smoke.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${1:-${BACKEND_URL:-http://localhost:8000}}"
TIMEOUT=10
PASS_COUNT=0
FAIL_COUNT=0

echo "=============================================="
echo "  EduStream Integration Smoke Test"
echo "=============================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Helper function to test endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local expected_status=$3
    local description=$4
    local auth_token=$5
    local body=$6

    local url="${BACKEND_URL}${path}"
    local curl_args="-s -o /dev/null -w %{http_code} --max-time $TIMEOUT"

    if [ -n "$auth_token" ]; then
        curl_args="$curl_args -H \"Authorization: Bearer $auth_token\""
    fi

    if [ -n "$body" ]; then
        curl_args="$curl_args -H \"Content-Type: application/json\" -d '$body'"
    fi

    # Execute curl
    local status
    if [ "$method" = "GET" ]; then
        status=$(eval "curl $curl_args \"$url\"")
    elif [ "$method" = "POST" ]; then
        status=$(eval "curl $curl_args -X POST \"$url\"")
    elif [ "$method" = "PATCH" ]; then
        status=$(eval "curl $curl_args -X PATCH \"$url\"")
    elif [ "$method" = "DELETE" ]; then
        status=$(eval "curl $curl_args -X DELETE \"$url\"")
    fi

    # Check result
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} $method $path → $status ($description)"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ FAIL${NC} $method $path → $status (expected $expected_status) ($description)"
        ((FAIL_COUNT++))
    fi
}

# Test helper for checking if endpoint exists (not 404)
test_exists() {
    local method=$1
    local path=$2
    local description=$3

    local url="${BACKEND_URL}${path}"
    local status
    status=$(curl -s -o /dev/null -w %{http_code} --max-time $TIMEOUT "$url")

    # 404 = endpoint doesn't exist, anything else = exists (even if auth required)
    if [ "$status" != "404" ]; then
        echo -e "${GREEN}✓ PASS${NC} $method $path → $status (exists) ($description)"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ FAIL${NC} $method $path → 404 (endpoint not found) ($description)"
        ((FAIL_COUNT++))
    fi
}

echo "=== Phase 1: Health Check ==="
echo ""

# Test health endpoint
test_endpoint "GET" "/health" "200" "Backend health check"

echo ""
echo "=== Phase 2: Public Endpoints ==="
echo ""

# Test public endpoints (no auth required)
test_endpoint "GET" "/api/v1/subjects" "200" "List subjects"
test_endpoint "GET" "/api/v1/tutors" "200" "List tutors"
test_endpoint "GET" "/docs" "200" "Swagger docs"
test_endpoint "GET" "/openapi.json" "200" "OpenAPI spec"

echo ""
echo "=== Phase 3: Auth Endpoints ==="
echo ""

# Test auth endpoints (should return 422 for missing body, not 404)
test_exists "POST" "/api/v1/auth/login" "Login endpoint exists"
test_exists "POST" "/api/v1/auth/register" "Register endpoint exists"
test_exists "POST" "/api/v1/auth/refresh" "Refresh endpoint exists"

echo ""
echo "=== Phase 4: Protected Endpoints (No Auth) ==="
echo ""

# These should return 401 (unauthorized), not 404 (not found)
test_endpoint "GET" "/api/v1/auth/me" "401" "Get current user (no auth)"
test_endpoint "GET" "/api/v1/bookings" "401" "List bookings (no auth)"
test_endpoint "GET" "/api/v1/messages/threads" "401" "List message threads (no auth)"
test_endpoint "GET" "/api/v1/notifications" "401" "List notifications (no auth)"
test_endpoint "GET" "/api/v1/favorites" "401" "List favorites (no auth)"

echo ""
echo "=== Phase 5: Version Prefix Test ==="
echo ""
echo "Testing that all routes require /v1/ prefix..."
echo ""

# These SHOULD return 404 (no route without /v1/)
echo "Expected 404s (correct behavior - no route without /v1/):"
test_endpoint "GET" "/api/messages/threads" "404" "Messages without /v1/ should 404"
test_endpoint "GET" "/api/notifications" "404" "Notifications without /v1/ should 404"
test_endpoint "GET" "/api/favorites" "404" "Favorites without /v1/ should 404"

echo ""
echo "=== Phase 6: CORS Preflight ==="
echo ""

# Test CORS preflight
cors_status=$(curl -s -o /dev/null -w %{http_code} --max-time $TIMEOUT \
    -X OPTIONS \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Authorization,Content-Type" \
    "${BACKEND_URL}/api/v1/subjects")

if [ "$cors_status" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} CORS preflight returns 200"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠ WARN${NC} CORS preflight returns $cors_status (may need CORS_ORIGINS config)"
fi

echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo ""
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}INTEGRATION TEST FAILED${NC}"
    echo ""
    echo "Common issues:"
    echo "  1. Backend not running: docker compose up -d backend"
    echo "  2. Wrong URL: Check BACKEND_URL environment variable"
    echo "  3. CORS not configured: Check CORS_ORIGINS in .env"
    echo ""
    exit 1
else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi
