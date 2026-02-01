#!/bin/bash
# =============================================================================
# CORS Smoke Test Script
# =============================================================================
# Run this script to verify CORS configuration is working correctly.
# Can be run locally or in CI pipelines.
#
# Usage:
#   ./scripts/cors-smoke-test.sh                    # Test against localhost:8000
#   ./scripts/cors-smoke-test.sh https://api.valsa.solutions  # Test against production
#   API_URL=http://localhost:8000 ./scripts/cors-smoke-test.sh
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed
# =============================================================================

set -e

# Configuration
API_URL="${1:-${API_URL:-http://localhost:8000}}"
ALLOWED_ORIGIN="${ALLOWED_ORIGIN:-http://localhost:3000}"
DISALLOWED_ORIGIN="http://evil.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# =============================================================================
# Helper Functions
# =============================================================================

log_test() {
    echo -e "\n${YELLOW}TEST:${NC} $1"
}

log_pass() {
    echo -e "${GREEN}PASS:${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}FAIL:${NC} $1"
    ((FAILED++))
}

check_header() {
    local response="$1"
    local header="$2"
    local expected="$3"

    actual=$(echo "$response" | grep -i "^$header:" | sed "s/^$header: //i" | tr -d '\r')

    if [ -z "$expected" ]; then
        # Check header is NOT present or not equal to a bad value
        if [ -z "$actual" ]; then
            return 0
        else
            return 1
        fi
    else
        if [ "$actual" == "$expected" ]; then
            return 0
        else
            echo "  Expected: $expected"
            echo "  Actual: $actual"
            return 1
        fi
    fi
}

# =============================================================================
# Tests
# =============================================================================

echo "=============================================="
echo "CORS Smoke Tests"
echo "=============================================="
echo "API URL: $API_URL"
echo "Allowed Origin: $ALLOWED_ORIGIN"
echo "=============================================="

# -----------------------------------------------------------------------------
# Test 1: Health endpoint (no CORS needed)
# -----------------------------------------------------------------------------
log_test "Health endpoint works without Origin header"

response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" == "200" ]; then
    log_pass "Health endpoint returned 200"
else
    log_fail "Health endpoint returned $status (expected 200)"
fi

# -----------------------------------------------------------------------------
# Test 2: CORS test endpoint from allowed origin
# -----------------------------------------------------------------------------
log_test "CORS test endpoint from allowed origin"

response=$(curl -s -i "$API_URL/api/v1/cors-test" \
    -H "Origin: $ALLOWED_ORIGIN")

if echo "$response" | grep -qi "access-control-allow-origin: $ALLOWED_ORIGIN"; then
    log_pass "Access-Control-Allow-Origin header present for allowed origin"
else
    log_fail "Access-Control-Allow-Origin header missing or incorrect"
    echo "$response" | grep -i "access-control"
fi

if echo "$response" | grep -qi "access-control-allow-credentials: true"; then
    log_pass "Access-Control-Allow-Credentials header is true"
else
    log_fail "Access-Control-Allow-Credentials header missing or false"
fi

# -----------------------------------------------------------------------------
# Test 3: OPTIONS preflight from allowed origin
# -----------------------------------------------------------------------------
log_test "OPTIONS preflight from allowed origin"

response=$(curl -s -i -X OPTIONS "$API_URL/api/v1/cors-test" \
    -H "Origin: $ALLOWED_ORIGIN" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Authorization")

status=$(echo "$response" | grep "HTTP/" | awk '{print $2}')

if [ "$status" == "200" ] || [ "$status" == "204" ]; then
    log_pass "Preflight returned $status"
else
    log_fail "Preflight returned $status (expected 200 or 204)"
fi

if echo "$response" | grep -qi "access-control-allow-origin: $ALLOWED_ORIGIN"; then
    log_pass "Preflight has Access-Control-Allow-Origin"
else
    log_fail "Preflight missing Access-Control-Allow-Origin"
fi

if echo "$response" | grep -qi "access-control-allow-methods:"; then
    log_pass "Preflight has Access-Control-Allow-Methods"
else
    log_fail "Preflight missing Access-Control-Allow-Methods"
fi

# -----------------------------------------------------------------------------
# Test 4: CORS test endpoint from disallowed origin
# -----------------------------------------------------------------------------
log_test "CORS test endpoint from disallowed origin"

response=$(curl -s -i "$API_URL/api/v1/cors-test" \
    -H "Origin: $DISALLOWED_ORIGIN")

if echo "$response" | grep -qi "access-control-allow-origin: $DISALLOWED_ORIGIN"; then
    log_fail "Access-Control-Allow-Origin should NOT be set to disallowed origin"
else
    log_pass "Disallowed origin correctly rejected"
fi

# -----------------------------------------------------------------------------
# Test 5: 404 endpoint includes CORS headers
# -----------------------------------------------------------------------------
log_test "404 response includes CORS headers"

response=$(curl -s -i "$API_URL/api/v1/nonexistent-endpoint-12345" \
    -H "Origin: $ALLOWED_ORIGIN")

status=$(echo "$response" | grep "HTTP/" | awk '{print $2}')

if [ "$status" == "404" ]; then
    log_pass "Got expected 404 status"
else
    log_fail "Expected 404, got $status"
fi

if echo "$response" | grep -qi "access-control-allow-origin: $ALLOWED_ORIGIN"; then
    log_pass "404 response has CORS headers"
else
    log_fail "404 response missing CORS headers (browser will show CORS error)"
fi

# -----------------------------------------------------------------------------
# Test 6: CORS debug info is useful
# -----------------------------------------------------------------------------
log_test "CORS debug endpoint returns useful info"

response=$(curl -s "$API_URL/api/v1/cors-test" \
    -H "Origin: $ALLOWED_ORIGIN")

if echo "$response" | grep -q "cors_debug"; then
    log_pass "Response contains cors_debug info"
else
    log_fail "Response missing cors_debug info"
fi

if echo "$response" | grep -q "origin_allowed.*true"; then
    log_pass "Origin correctly identified as allowed"
else
    log_fail "Origin not correctly identified as allowed"
fi

# -----------------------------------------------------------------------------
# Test 7: Vary header is present (for caching)
# -----------------------------------------------------------------------------
log_test "Vary header includes Origin"

response=$(curl -s -i "$API_URL/api/v1/cors-test" \
    -H "Origin: $ALLOWED_ORIGIN")

if echo "$response" | grep -qi "vary:.*origin"; then
    log_pass "Vary header includes Origin (good for caching)"
else
    log_fail "Vary header missing Origin (may cause caching issues)"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "=============================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Some tests failed. See docs/CORS_DEBUGGING.md for troubleshooting.${NC}"
    exit 1
else
    echo -e "${GREEN}All CORS tests passed!${NC}"
    exit 0
fi
