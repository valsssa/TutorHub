#!/bin/bash
# Frontend linting script
# Usage: ./scripts/lint-frontend.sh [--fix]

set -e

cd "$(dirname "$0")/.."

FRONTEND_DIR="frontend"
FIX_MODE=false

# Parse arguments
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "🔍 Running frontend linting checks..."
echo ""

# 1. ESLint - JavaScript/TypeScript linter
echo "📋 Running ESLint..."
if [ "$FIX_MODE" = true ]; then
    docker compose exec frontend npm run lint:fix
else
    docker compose exec frontend npm run lint
fi
echo "✅ ESLint check complete"
echo ""

# 2. Prettier - Code formatter
echo "📝 Running Prettier..."
if [ "$FIX_MODE" = true ]; then
    docker compose exec frontend npm run format:fix
else
    docker compose exec frontend npm run format:check
fi
echo "✅ Prettier check complete"
echo ""

# 3. TypeScript - Type checker
echo "🔎 Running TypeScript type checker..."
docker compose exec frontend npm run type-check
echo "✅ Type check complete"
echo ""

# 4. Next.js - Build check
echo "🏗️  Running Next.js build check..."
docker compose exec frontend npm run build
echo "✅ Build check complete"
echo ""

echo "✨ Frontend linting complete!"
