#!/bin/bash
# =============================================================================
# Instant Backend Start - Fastest backend-only startup
# Usage: ./scripts/instant-backend.sh
# =============================================================================

set -e

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "Starting backend in 10 seconds..."

# Start DB and Redis first (parallel)
docker compose -f docker-compose.fast.yml up db redis -d

# Wait minimal time for DB
echo "Waiting for database..."
sleep 3

# Start backend with existing image (no rebuild)
docker compose -f docker-compose.fast.yml up backend -d

echo ""
echo "Backend running at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "Logs: docker compose -f docker-compose.fast.yml logs -f backend"
