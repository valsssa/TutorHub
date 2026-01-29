# =============================================================================
# Makefile - Quick Commands for EduStream
# =============================================================================

.PHONY: help dev minimal full prod build rebuild stop clean logs test lint

# Default target
help:
	@echo "EduStream Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start dev environment (backend + frontend + db)"
	@echo "  make minimal    - Start minimal (backend + db + redis only)"
	@echo "  make full       - Start all services including Celery"
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

# Compose files
COMPOSE_FAST=docker-compose.fast.yml
COMPOSE_PROD=docker-compose.prod.yml

# =============================================================================
# Development
# =============================================================================

dev:
	docker compose -f $(COMPOSE_FAST) up db redis minio backend frontend -d
	@echo ""
	@echo "Services started!"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"

minimal:
	docker compose -f $(COMPOSE_FAST) up db redis backend -d
	@echo ""
	@echo "Minimal services started!"
	@echo "  Backend: http://localhost:8000"

full:
	docker compose -f $(COMPOSE_FAST) --profile workers up -d
	@echo ""
	@echo "All services started!"

backend:
	docker compose -f $(COMPOSE_FAST) up db redis backend -d

frontend:
	docker compose -f $(COMPOSE_FAST) up frontend -d

# =============================================================================
# Build
# =============================================================================

build:
	docker compose -f $(COMPOSE_FAST) build --parallel

rebuild:
	docker compose -f $(COMPOSE_FAST) up -d --build

prod:
	docker compose -f $(COMPOSE_PROD) build --parallel

prod-deploy:
	docker compose -f $(COMPOSE_PROD) up -d --build

# =============================================================================
# Management
# =============================================================================

stop:
	docker compose -f $(COMPOSE_FAST) down
	docker compose -f $(COMPOSE_PROD) down 2>/dev/null || true

clean:
	docker compose -f $(COMPOSE_FAST) down -v
	docker compose -f $(COMPOSE_PROD) down -v 2>/dev/null || true
	docker system prune -f

logs:
	docker compose -f $(COMPOSE_FAST) logs -f

logs-b:
	docker compose -f $(COMPOSE_FAST) logs -f backend

logs-f:
	docker compose -f $(COMPOSE_FAST) logs -f frontend

status:
	@echo "Running containers:"
	docker compose -f $(COMPOSE_FAST) ps
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
	docker compose -f $(COMPOSE_FAST) exec db psql -U postgres -d authapp

db-reset:
	docker compose -f $(COMPOSE_FAST) down -v
	docker compose -f $(COMPOSE_FAST) up db -d

# =============================================================================
# Quick shortcuts
# =============================================================================

up: dev
down: stop
restart: stop dev
