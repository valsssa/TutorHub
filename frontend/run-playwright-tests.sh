#!/bin/bash

# Playwright Test Runner Script
# Runs E2E tests with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

# Default values
MODE="default"
BROWSER="chromium"
HEADED=false
DEBUG=false
UI=false
WORKERS="auto"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ui)
            UI=true
            shift
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --grep)
            GREP="$2"
            shift 2
            ;;
        --file)
            TEST_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Playwright Test Runner"
            echo ""
            echo "Usage: ./run-playwright-tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --ui              Run tests in UI mode (interactive)"
            echo "  --headed          Run tests in headed mode (show browser)"
            echo "  --debug           Run tests in debug mode"
            echo "  --browser NAME    Specify browser (chromium, firefox, webkit)"
            echo "  --workers N       Number of parallel workers"
            echo "  --grep PATTERN    Run tests matching pattern"
            echo "  --file PATH       Run specific test file"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run-playwright-tests.sh                    # Run all tests"
            echo "  ./run-playwright-tests.sh --ui               # Interactive mode"
            echo "  ./run-playwright-tests.sh --headed           # Show browser"
            echo "  ./run-playwright-tests.sh --grep 'login'     # Run login tests"
            echo "  ./run-playwright-tests.sh --file e2e/auth-flow.spec.ts"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to frontend directory
cd "$(dirname "$0")"

print_info "Playwright E2E Test Runner"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Running npm install..."
    npm install
fi

# Build command
CMD="npx playwright test"

# Add options
if [ "$UI" = true ]; then
    CMD="$CMD --ui"
    print_info "Running in UI mode (interactive)"
elif [ "$DEBUG" = true ]; then
    CMD="$CMD --debug"
    print_info "Running in debug mode"
else
    # Add reporter for non-interactive modes
    CMD="$CMD --reporter=list,html"
fi

if [ "$HEADED" = true ]; then
    CMD="$CMD --headed"
    print_info "Running in headed mode (browser visible)"
fi

if [ -n "$BROWSER" ] && [ "$BROWSER" != "chromium" ]; then
    CMD="$CMD --project=$BROWSER"
    print_info "Using browser: $BROWSER"
fi

if [ -n "$WORKERS" ] && [ "$WORKERS" != "auto" ]; then
    CMD="$CMD --workers=$WORKERS"
    print_info "Using $WORKERS worker(s)"
fi

if [ -n "$GREP" ]; then
    CMD="$CMD --grep \"$GREP\""
    print_info "Running tests matching: $GREP"
fi

if [ -n "$TEST_FILE" ]; then
    CMD="$CMD $TEST_FILE"
    print_info "Running test file: $TEST_FILE"
fi

echo ""
print_info "Executing: $CMD"
echo ""

# Run tests
if eval $CMD; then
    echo ""
    print_success "All tests passed!"
    
    # Show report option
    if [ "$UI" = false ] && [ "$DEBUG" = false ]; then
        echo ""
        print_info "View detailed report: npm run test:e2e:report"
    fi
    
    exit 0
else
    EXIT_CODE=$?
    echo ""
    print_error "Tests failed with exit code: $EXIT_CODE"
    
    # Show report on failure
    if [ "$UI" = false ] && [ "$DEBUG" = false ]; then
        echo ""
        print_info "View detailed report: npm run test:e2e:report"
    fi
    
    exit $EXIT_CODE
fi
