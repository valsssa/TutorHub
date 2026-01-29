#!/bin/bash
# =============================================================================
# Quick Start Script - Fastest way to get the app running
# Usage: ./scripts/quick-start.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=========================================="
echo "  EduStream Quick Start"
echo "=========================================="
echo -e "${NC}"

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Pulling base images...${NC}"
docker pull postgres:17-alpine &
docker pull redis:7-alpine &
docker pull node:20-alpine &
docker pull python:3.12-slim &
wait

echo -e "${YELLOW}Step 2: Building application images...${NC}"
docker compose -f docker-compose.fast.yml build --parallel

echo -e "${YELLOW}Step 3: Starting services...${NC}"
docker compose -f docker-compose.fast.yml up db redis -d

echo -e "${YELLOW}Step 4: Waiting for database...${NC}"
sleep 3

docker compose -f docker-compose.fast.yml up minio backend -d

echo -e "${YELLOW}Step 5: Waiting for backend...${NC}"
sleep 5

docker compose -f docker-compose.fast.yml up frontend -d

echo ""
echo -e "${GREEN}=========================================="
echo "  All services are starting!"
echo "==========================================${NC}"
echo ""
echo "  Backend API:    http://localhost:8000"
echo "  Frontend:       http://localhost:3000"
echo "  MinIO Console:  http://localhost:9001"
echo "  API Docs:       http://localhost:8000/docs"
echo ""
echo "Default Credentials:"
echo "  Admin:   admin@example.com / admin123"
echo "  Tutor:   tutor@example.com / tutor123"
echo "  Student: student@example.com / student123"
echo ""
echo -e "${YELLOW}View logs: docker compose -f docker-compose.fast.yml logs -f${NC}"
echo ""
