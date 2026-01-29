#!/bin/bash
# =============================================================================
# Fast Development Startup Script
# Usage: ./scripts/dev.sh [mode]
#
# Modes:
#   minimal  - Backend + DB + Redis only (fastest)
#   dev      - Backend + Frontend + DB + Redis + MinIO
#   full     - All services including Celery workers
#   frontend - Frontend only (assumes backend running)
#   backend  - Backend only (assumes DB running)
# =============================================================================

set -e

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

MODE=${1:-dev}
COMPOSE_FILE="docker-compose.fast.yml"

echo "=========================================="
echo "EduStream Fast Development"
echo "Mode: $MODE"
echo "=========================================="

case $MODE in
  minimal)
    echo "Starting minimal services (backend + db + redis)..."
    docker compose -f $COMPOSE_FILE up db redis backend -d
    ;;

  dev)
    echo "Starting development services..."
    docker compose -f $COMPOSE_FILE up db redis minio backend frontend -d
    ;;

  full)
    echo "Starting all services including workers..."
    docker compose -f $COMPOSE_FILE --profile workers up -d
    ;;

  frontend)
    echo "Starting frontend only..."
    docker compose -f $COMPOSE_FILE up frontend -d
    ;;

  backend)
    echo "Starting backend only..."
    docker compose -f $COMPOSE_FILE up backend -d
    ;;

  build)
    echo "Building all images..."
    docker compose -f $COMPOSE_FILE build --parallel
    ;;

  rebuild)
    echo "Rebuilding and starting..."
    docker compose -f $COMPOSE_FILE up -d --build
    ;;

  stop)
    echo "Stopping all services..."
    docker compose -f $COMPOSE_FILE down
    ;;

  logs)
    echo "Showing logs..."
    docker compose -f $COMPOSE_FILE logs -f
    ;;

  clean)
    echo "Cleaning up (removing volumes)..."
    docker compose -f $COMPOSE_FILE down -v
    docker system prune -f
    ;;

  *)
    echo "Unknown mode: $MODE"
    echo "Usage: ./scripts/dev.sh [minimal|dev|full|frontend|backend|build|rebuild|stop|logs|clean]"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "Services Status:"
docker compose -f $COMPOSE_FILE ps
echo "=========================================="
echo ""
echo "URLs:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  MinIO:    http://localhost:9001"
echo "=========================================="
