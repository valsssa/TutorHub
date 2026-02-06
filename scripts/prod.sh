#!/bin/bash
# =============================================================================
# Production Build & Deploy Script
# Usage: ./scripts/prod.sh [command]
#
# Commands:
#   build    - Build production images
#   deploy   - Build and start production
#   start    - Start production (no rebuild)
#   stop     - Stop production
#   logs     - View logs
#   status   - Show status
# =============================================================================

set -e

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

COMMAND=${1:-deploy}
COMPOSE_FILE="docker-compose.prod.yml"

echo "=========================================="
echo "EduStream Production"
echo "Command: $COMMAND"
echo "=========================================="

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and configure it."
    exit 1
fi

case $COMMAND in
  build)
    echo "Building production images..."
    docker compose -f $COMPOSE_FILE build --parallel --no-cache
    echo "Tagging images..."
    docker tag edustream-backend:prod edustream-backend:latest
    docker tag edustream-frontend:prod edustream-frontend:latest
    ;;

  deploy)
    echo "Building and deploying..."
    docker compose -f $COMPOSE_FILE up -d --build
    ;;

  start)
    echo "Starting production services..."
    docker compose -f $COMPOSE_FILE up -d
    ;;

  stop)
    echo "Stopping production services..."
    docker compose -f $COMPOSE_FILE down
    ;;

  restart)
    echo "Restarting services..."
    docker compose -f $COMPOSE_FILE restart
    ;;

  logs)
    SERVICE=${2:-}
    if [ -n "$SERVICE" ]; then
      docker compose -f $COMPOSE_FILE logs -f $SERVICE
    else
      docker compose -f $COMPOSE_FILE logs -f
    fi
    ;;

  status)
    docker compose -f $COMPOSE_FILE ps
    echo ""
    echo "Image sizes:"
    docker images | grep edustream
    ;;

  *)
    echo "Unknown command: $COMMAND"
    echo "Usage: ./scripts/prod.sh [build|deploy|start|stop|restart|logs|status]"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "Production Status:"
docker compose -f $COMPOSE_FILE ps
echo "=========================================="
