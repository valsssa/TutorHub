#!/bin/bash
# Run all linting checks
# Usage: ./scripts/lint-all.sh [--fix]

set -e

cd "$(dirname "$0")/.."

FIX_ARG=""
if [[ "$1" == "--fix" ]]; then
    FIX_ARG="--fix"
    echo "🔧 Running linters in FIX mode..."
else
    echo "🔍 Running linters in CHECK mode..."
fi
echo ""

# Run backend linting
echo "════════════════════════════════════════"
echo "         BACKEND LINTING"
echo "════════════════════════════════════════"
./scripts/lint-backend.sh $FIX_ARG

echo ""
echo "════════════════════════════════════════"
echo "         FRONTEND LINTING"
echo "════════════════════════════════════════"
./scripts/lint-frontend.sh $FIX_ARG

echo ""
echo "════════════════════════════════════════"
echo "✨ All linting checks complete!"
echo "════════════════════════════════════════"
