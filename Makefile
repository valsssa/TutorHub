# =============================================================================
# Makefile - Quick Commands for EduStream
# =============================================================================

.PHONY: help dev minimal full build rebuild stop clean logs test lint

# Default target
help:
	@echo "EduStream Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start dev environment (backend + frontend + db)"
	@echo "  make minimal    - Start minimal (backend + db + redis only)"
	@echo "  make full       - Start all services including Celery + MinIO"
	@echo "  make backend    - Start backend only"
	@echo "  make frontend   - Start frontend only"
	@echo ""
	@echo "Build:"
	@echo "  make build      - Build all images"
	@echo "  make rebuild    - Rebuild and restart"
	@echo "  make prod       - Build production images"
	@echo ""
	@echo "Management:"
	@echo "  make stop       - Stop all services"
	@echo "  make clean      - Stop and remove volumes"
	@echo "  make logs       - View logs (all services)"
	@echo "  make logs-b     - View backend logs"
	@echo "  make logs-f     - View frontend logs"
	@echo "  make status     - Show running services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo ""

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# =============================================================================
# Development
# =============================================================================

dev:
	docker compose up -d
	@echo ""
	@echo "Services started!"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"

minimal:
	docker compose up db redis backend -d
	@echo ""
	@echo "Minimal services started!"
	@echo "  Backend: http://localhost:8000"

full:
	docker compose --profile full up -d
	@echo ""
	@echo "All services started!"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  MinIO:    http://localhost:9001"

backend:
	docker compose up db redis backend -d

frontend:
	docker compose up frontend -d

storage:
	docker compose --profile storage up -d

workers:
	docker compose --profile workers up -d

# =============================================================================
# Build
# =============================================================================

build:
	docker compose build --parallel

rebuild:
	docker compose up -d --build

prod:
	docker compose build backend --build-arg TARGET=production
	docker compose build frontend --build-arg TARGET=production

# =============================================================================
# Management
# =============================================================================

stop:
	docker compose down

clean:
	docker compose down -v
	docker system prune -f

logs:
	docker compose logs -f

logs-b:
	docker compose logs -f backend

logs-f:
	docker compose logs -f frontend

status:
	@echo "Running containers:"
	docker compose ps
	@echo ""
	@echo "Images:"
	docker images | grep edustream || true

# =============================================================================
# Testing & Quality
# =============================================================================

test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

lint:
	./scripts/lint-all.sh

lint-fix:
	./scripts/lint-all.sh --fix

# =============================================================================
# Database
# =============================================================================

db-shell:
	docker compose exec db psql -U postgres -d authapp

db-reset:
	docker compose down -v
	docker compose up db -d

# =============================================================================
# Quick shortcuts
# =============================================================================

up: dev
down: stop
restart: stop dev
