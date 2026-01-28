#!/bin/bash

###############################################################################
# COMPREHENSIVE TEST EXECUTION SCRIPT
###############################################################################
#
# This script runs the complete test suite including:
# - Backend unit tests
# - Backend integration tests
# - Frontend unit tests
# - Frontend component tests
# - End-to-end (E2E) tests
# - Test coverage reports
#
# Usage:
#   ./RUN_ALL_TESTS_COMPREHENSIVE.sh [OPTIONS]
#
# Options:
#   --backend-only    Run only backend tests
#   --frontend-only   Run only frontend tests
#   --e2e-only        Run only E2E tests
#   --unit-only       Run only unit tests (backend + frontend)
#   --integration     Run integration tests
#   --coverage        Generate coverage reports
#   --fast            Skip slow tests (for quick validation)
#   --verbose         Show detailed test output
#   --clean           Clean up test artifacts before running
#   --help            Show this help message
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_BACKEND=true
RUN_FRONTEND=true
RUN_E2E=true
RUN_UNIT=true
RUN_INTEGRATION=true
GENERATE_COVERAGE=false
FAST_MODE=false
VERBOSE=false
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --backend-only)
      RUN_FRONTEND=false
      RUN_E2E=false
      shift
      ;;
    --frontend-only)
      RUN_BACKEND=false
      RUN_E2E=false
      shift
      ;;
    --e2e-only)
      RUN_BACKEND=false
      RUN_FRONTEND=false
      RUN_UNIT=false
      RUN_INTEGRATION=false
      shift
      ;;
    --unit-only)
      RUN_INTEGRATION=false
      RUN_E2E=false
      shift
      ;;
    --integration)
      RUN_UNIT=false
      RUN_E2E=false
      shift
      ;;
    --coverage)
      GENERATE_COVERAGE=true
      shift
      ;;
    --fast)
      FAST_MODE=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    --help)
      head -n 35 "$0" | tail -n +3
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

###############################################################################
# Helper Functions
###############################################################################

print_header() {
  echo ""
  echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║${NC} $1"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

check_docker() {
  if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
  fi

  if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
  fi

  print_success "Docker is running"
}

###############################################################################
# Cleanup Function
###############################################################################

cleanup_test_artifacts() {
  print_header "Cleaning Test Artifacts"

  # Stop and remove test containers
  print_info "Stopping test containers..."
  docker compose -f docker-compose.test.yml down -v 2>/dev/null || true

  # Remove coverage reports
  if [ -d "backend/htmlcov" ]; then
    print_info "Removing backend coverage reports..."
    rm -rf backend/htmlcov backend/.coverage
  fi

  if [ -d "frontend/coverage" ]; then
    print_info "Removing frontend coverage reports..."
    rm -rf frontend/coverage
  fi

  # Remove pytest cache
  if [ -d "backend/.pytest_cache" ]; then
    print_info "Removing pytest cache..."
    rm -rf backend/.pytest_cache
  fi

  # Remove Jest cache
  if [ -d "frontend/.jest" ]; then
    print_info "Removing Jest cache..."
    rm -rf frontend/.jest
  fi

  # Remove E2E artifacts
  if [ -d "tests/e2e/screenshots" ]; then
    print_info "Removing E2E screenshots..."
    rm -rf tests/e2e/screenshots
  fi

  if [ -d "tests/e2e/videos" ]; then
    print_info "Removing E2E videos..."
    rm -rf tests/e2e/videos
  fi

  print_success "Cleanup completed"
}

###############################################################################
# Test Execution Functions
###############################################################################

run_backend_tests() {
  print_header "Running Backend Tests"

  local pytest_args=""

  if [ "$FAST_MODE" = true ]; then
    pytest_args="$pytest_args -m 'not slow'"
    print_info "Fast mode: Skipping slow tests"
  fi

  if [ "$VERBOSE" = true ]; then
    pytest_args="$pytest_args -v"
  else
    pytest_args="$pytest_args -q"
  fi

  if [ "$GENERATE_COVERAGE" = true ]; then
    pytest_args="$pytest_args --cov=backend --cov-report=html --cov-report=term"
    print_info "Coverage reporting enabled"
  fi

  # Run unit tests
  if [ "$RUN_UNIT" = true ]; then
    print_info "Running backend unit tests..."
    docker compose -f docker-compose.test.yml up --build --abort-on-container-exit backend-tests

    if [ $? -eq 0 ]; then
      print_success "Backend unit tests passed"
    else
      print_error "Backend unit tests failed"
      return 1
    fi
  fi

  # Run integration tests
  if [ "$RUN_INTEGRATION" = true ]; then
    print_info "Running backend integration tests..."
    docker compose -f docker-compose.test.yml run --rm backend pytest -m integration $pytest_args

    if [ $? -eq 0 ]; then
      print_success "Backend integration tests passed"
    else
      print_error "Backend integration tests failed"
      return 1
    fi
  fi

  return 0
}

run_frontend_tests() {
  print_header "Running Frontend Tests"

  local jest_args=""

  if [ "$VERBOSE" = true ]; then
    jest_args="$jest_args --verbose"
  fi

  if [ "$GENERATE_COVERAGE" = true ]; then
    jest_args="$jest_args --coverage"
    print_info "Coverage reporting enabled"
  fi

  # Run frontend tests
  print_info "Running frontend tests..."
  docker compose -f docker-compose.test.yml up --build --abort-on-container-exit frontend-tests

  if [ $? -eq 0 ]; then
    print_success "Frontend tests passed"
    return 0
  else
    print_error "Frontend tests failed"
    return 1
  fi
}

run_e2e_tests() {
  print_header "Running End-to-End Tests"

  print_info "Starting services for E2E tests..."

  # Start backend and frontend services
  docker compose -f docker-compose.test.yml up -d backend frontend db

  # Wait for services to be ready
  print_info "Waiting for services to be ready..."
  sleep 10

  # Check backend health
  if ! curl -f http://localhost:8000/health &> /dev/null; then
    print_error "Backend is not responding"
    docker compose -f docker-compose.test.yml logs backend
    docker compose -f docker-compose.test.yml down
    return 1
  fi

  print_success "Backend is ready"

  # Check frontend health
  if ! curl -f http://localhost:3000 &> /dev/null; then
    print_error "Frontend is not responding"
    docker compose -f docker-compose.test.yml logs frontend
    docker compose -f docker-compose.test.yml down
    return 1
  fi

  print_success "Frontend is ready"

  # Run E2E tests
  print_info "Running E2E tests..."
  docker compose -f docker-compose.test.yml up --abort-on-container-exit e2e-tests

  local exit_code=$?

  # Collect E2E artifacts
  if [ -d "tests/e2e/screenshots" ]; then
    print_info "E2E screenshots saved to: tests/e2e/screenshots/"
  fi

  if [ -d "tests/e2e/videos" ]; then
    print_info "E2E videos saved to: tests/e2e/videos/"
  fi

  # Stop services
  docker compose -f docker-compose.test.yml down

  if [ $exit_code -eq 0 ]; then
    print_success "E2E tests passed"
    return 0
  else
    print_error "E2E tests failed"
    return 1
  fi
}

###############################################################################
# Test Summary
###############################################################################

generate_test_summary() {
  print_header "Test Summary"

  local total_passed=$1
  local total_failed=$2

  if [ $total_failed -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  ALL TESTS PASSED! ✓                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
  else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                  SOME TESTS FAILED ✗                           ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
  fi

  echo ""
  echo "Test Results:"
  echo "  Passed: $total_passed"
  echo "  Failed: $total_failed"
  echo ""

  if [ "$GENERATE_COVERAGE" = true ]; then
    echo "Coverage Reports:"

    if [ -f "backend/htmlcov/index.html" ]; then
      echo "  Backend: file://$(pwd)/backend/htmlcov/index.html"
    fi

    if [ -f "frontend/coverage/lcov-report/index.html" ]; then
      echo "  Frontend: file://$(pwd)/frontend/coverage/lcov-report/index.html"
    fi

    echo ""
  fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
  local start_time=$(date +%s)
  local passed_count=0
  local failed_count=0

  print_header "Comprehensive Test Suite"
  print_info "Test run started at: $(date)"

  # Check Docker
  check_docker

  # Cleanup if requested
  if [ "$CLEAN" = true ]; then
    cleanup_test_artifacts
  fi

  # Run backend tests
  if [ "$RUN_BACKEND" = true ]; then
    if run_backend_tests; then
      ((passed_count++))
    else
      ((failed_count++))
    fi
  fi

  # Run frontend tests
  if [ "$RUN_FRONTEND" = true ]; then
    if run_frontend_tests; then
      ((passed_count++))
    else
      ((failed_count++))
    fi
  fi

  # Run E2E tests
  if [ "$RUN_E2E" = true ]; then
    if run_e2e_tests; then
      ((passed_count++))
    else
      ((failed_count++))
    fi
  fi

  # Calculate duration
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  local minutes=$((duration / 60))
  local seconds=$((duration % 60))

  # Generate summary
  generate_test_summary $passed_count $failed_count

  print_info "Test run completed at: $(date)"
  print_info "Total duration: ${minutes}m ${seconds}s"

  # Exit with appropriate code
  if [ $failed_count -eq 0 ]; then
    exit 0
  else
    exit 1
  fi
}

# Run main function
main
