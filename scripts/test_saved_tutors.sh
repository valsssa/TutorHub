#!/bin/bash

# Test runner for saved tutors functionality
# This script runs all tests related to saved tutors feature

set -e

echo "🧪 Running Saved Tutors Tests"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to run command and capture result
run_test() {
    local test_name=$1
    local command=$2

    echo ""
    print_status "info" "Running $test_name..."

    if eval "$command"; then
        print_status "success" "$test_name passed"
        return 0
    else
        print_status "error" "$test_name failed"
        return 1
    fi
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_status "error" "Docker is not running. Please start Docker first."
    exit 1
fi

# Backend API Tests
echo ""
print_status "info" "Starting Backend API Tests..."

# Wait for services to be ready
print_status "info" "Waiting for services to be ready..."
timeout=60
counter=0
while ! curl -s http://localhost:8000/docs > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_status "error" "Backend service did not start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo "Waiting for backend... ($counter/$timeout seconds)"
done

print_status "success" "Backend is ready"

run_test "Backend Favorites API Tests" "cd backend && python -m pytest tests/test_favorites_api.py -v"

# Frontend Tests
echo ""
print_status "info" "Starting Frontend Tests..."

# Wait for frontend to be ready
counter=0
while ! curl -s http://localhost:3000 > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_status "error" "Frontend service did not start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo "Waiting for frontend... ($counter/$timeout seconds)"
done

print_status "success" "Frontend is ready"

run_test "Frontend Saved Tutors Page Tests" "cd frontend && npm test -- --testPathPattern=saved-tutors.test.tsx --watchAll=false"
run_test "Frontend Tutor Profile Favorites Tests" "cd frontend && npm test -- --testPathPattern=tutor-profile-favorites.test.tsx --watchAll=false"
run_test "Frontend Favorites API Tests" "cd frontend && npm test -- --testPathPattern=favorites-api.test.ts --watchAll=false"

# E2E Tests (if Playwright is available)
echo ""
print_status "info" "Checking for E2E Tests..."

if command -v npx > /dev/null 2>&1 && [ -f "frontend/package.json" ] && grep -q "playwright" "frontend/package.json"; then
    print_status "info" "Running E2E Tests..."
    run_test "E2E Saved Tutors Workflow Tests" "cd frontend && npx playwright test tests/e2e/test_saved_tutors_workflow.py --headed=false"
else
    print_status "warning" "E2E tests skipped - Playwright not available or not configured"
fi

# Manual test instructions
echo ""
print_status "info" "Manual Testing Instructions:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Login as a student (student@example.com / student123)"
echo "3. Browse tutors at http://localhost:3000/tutors"
echo "4. Click the heart icon on a tutor profile to save them"
echo "5. Check your saved tutors at http://localhost:3000/saved-tutors"
echo "6. Verify the saved tutor appears in the list"
echo "7. Click the heart icon again to remove from favorites"
echo "8. Verify the tutor is removed from the saved list"

echo ""
print_status "success" "All automated tests completed!"
print_status "info" "Please perform manual testing as described above."

echo ""
echo "📊 Test Summary:"
echo "- Backend API Tests: ✅ Completed"
echo "- Frontend Component Tests: ✅ Completed"
echo "- E2E Tests: ⚠️  May require Playwright setup"
echo "- Manual Testing: 📋 Required for complete validation"

echo ""
print_status "success" "Saved Tutors feature testing completed!"