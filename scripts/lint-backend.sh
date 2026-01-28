#!/bin/bash
# Backend linting script
# Usage: ./scripts/lint-backend.sh [--fix]

set -e

cd "$(dirname "$0")/.."

BACKEND_DIR="backend"
FIX_MODE=false

# Parse arguments
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "🔍 Running backend linting checks..."
echo ""

# 1. Ruff - Fast Python linter (replaces flake8, isort, pyupgrade)
echo "📋 Running Ruff linter..."
if [ "$FIX_MODE" = true ]; then
    docker compose exec backend ruff check --fix "$BACKEND_DIR" || echo "⚠️  Ruff found issues (fixed where possible)"
else
    docker compose exec backend ruff check "$BACKEND_DIR"
fi
echo "✅ Ruff check complete"
echo ""

# 2. Ruff format - Code formatter (replaces black)
echo "📝 Running Ruff formatter..."
if [ "$FIX_MODE" = true ]; then
    docker compose exec backend ruff format "$BACKEND_DIR"
    echo "✅ Code formatted"
else
    docker compose exec backend ruff format --check "$BACKEND_DIR"
    echo "✅ Format check complete"
fi
echo ""

# 3. MyPy - Static type checker
echo "🔎 Running MyPy type checker..."
docker compose exec backend mypy "$BACKEND_DIR" --config-file mypy.ini || echo "⚠️  MyPy found type issues"
echo "✅ Type check complete"
echo ""

# 4. Bandit - Security linter
echo "🔒 Running Bandit security scanner..."
docker compose exec backend bandit -c .bandit.yaml -r "$BACKEND_DIR" || echo "⚠️  Bandit found security issues"
echo "✅ Security scan complete"
echo ""

# 5. Safety - Check dependencies for vulnerabilities
echo "🛡️  Running Safety dependency scanner..."
docker compose exec backend safety check --json || echo "⚠️  Safety found vulnerable dependencies"
echo "✅ Dependency scan complete"
echo ""

echo "✨ Backend linting complete!"
