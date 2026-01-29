# EduStream Docker Guide

Complete guide to run EduStream with Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Service Profiles](#service-profiles)
- [Common Commands](#common-commands)
- [Makefile Shortcuts](#makefile-shortcuts)
- [Services & Ports](#services--ports)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

---

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values (optional for local dev)
# Default values work for local development
```

### 2. Start Application

```bash
# Basic setup (db, redis, backend, frontend)
docker compose up -d

# OR full setup with file uploads + background tasks
docker compose --profile full up -d --build
```

### 3. Verify Services

```bash
# Check all services are running
docker compose ps

# Test backend health
curl http://localhost:8000/health

# Expected output: {"status":"healthy"}
```

### 4. Access Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 (if using `--profile storage` or `--profile full`) |

---

## Service Profiles

Docker Compose profiles allow you to start different combinations of services.

### Available Profiles

| Profile | Additional Services | Use Case |
|---------|---------------------|----------|
| (none) | db, redis, backend, frontend | Basic development |
| `storage` | + MinIO | File uploads (avatars, attachments) |
| `workers` | + Celery worker, Celery beat | Background tasks (booking auto-transitions) |
| `full` | + MinIO, Celery worker, Celery beat | Complete setup |

### Profile Commands

```bash
# Basic (no file uploads, no background tasks)
docker compose up -d

# With file uploads only
docker compose --profile storage up -d

# With background tasks only
docker compose --profile workers up -d

# Full setup (recommended for complete functionality)
docker compose --profile full up -d

# Combine profiles manually
docker compose --profile storage --profile workers up -d

# Build and start
docker compose --profile full up -d --build

# Rebuild specific service
docker compose --profile full up -d --build backend
```

### When to Use Each Profile

| Scenario | Recommended Command |
|----------|---------------------|
| Quick frontend/backend testing | `docker compose up -d` |
| Testing file uploads (avatars) | `docker compose --profile storage up -d` |
| Testing booking auto-expiration | `docker compose --profile workers up -d` |
| Full application testing | `docker compose --profile full up -d` |
| Production-like environment | `docker compose --profile full up -d` |

---

## Common Commands

### Starting Services

```bash
# Start with default profile
docker compose up -d

# Start with full profile
docker compose --profile full up -d

# Start and rebuild images
docker compose --profile full up -d --build

# Start specific services only
docker compose up db redis backend -d
```

### Stopping Services

```bash
# Stop all services (preserves data volumes)
docker compose down

# Stop and remove all data (clean slate)
docker compose down -v

# Stop specific service
docker compose stop backend
```

### Viewing Logs

```bash
# All services (follow mode)
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f celery-worker

# Last 100 lines
docker compose logs --tail=100 backend

# Without follow (snapshot)
docker compose logs backend
```

### Rebuilding

```bash
# Rebuild all images
docker compose build

# Rebuild specific service
docker compose build backend
docker compose build frontend

# Rebuild without cache (fresh build)
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --build
```

### Database Operations

```bash
# Access PostgreSQL shell
docker compose exec db psql -U postgres -d authapp

# Run SQL file
docker compose exec -T db psql -U postgres -d authapp < script.sql

# Backup database
docker compose exec db pg_dump -U postgres authapp > backup.sql

# Restore database
docker compose exec -T db psql -U postgres -d authapp < backup.sql

# Reset database (warning: deletes all data)
docker compose down -v
docker compose up db -d
```

### Container Access

```bash
# Backend shell (bash)
docker compose exec backend bash

# Frontend shell (sh - Alpine)
docker compose exec frontend sh

# Database shell
docker compose exec db psql -U postgres -d authapp

# Redis CLI
docker compose exec redis redis-cli
```

### Status & Health

```bash
# View running containers with health status
docker compose ps

# View resource usage
docker stats

# View container details
docker compose inspect backend
```

---

## Makefile Shortcuts

The Makefile provides convenient shortcuts:

```bash
# Show all available commands
make help

# Development
make dev          # Start db, redis, backend, frontend
make minimal      # Start db, redis, backend only
make full         # Start all services (--profile full)
make backend      # Start backend services only
make frontend     # Start frontend only

# Build
make build        # Build all images
make rebuild      # Rebuild and restart

# Management
make stop         # Stop all services
make clean        # Stop and remove volumes
make logs         # View all logs
make logs-b       # View backend logs
make logs-f       # View frontend logs
make status       # Show running services

# Database
make db-shell     # Open PostgreSQL shell
make db-reset     # Reset database (deletes data)

# Testing
make test         # Run test suite
make lint         # Run linting
```

---

## Services & Ports

### Core Services (Always Started)

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| PostgreSQL | edustream-db | 5432 | Primary database |
| Redis | edustream-redis | 6379 | Cache, rate limiting, Celery broker |
| Backend | edustream-backend | 8000 | FastAPI REST API |
| Frontend | edustream-frontend | 3000 | Next.js web application |

### Optional Services (Profile-Based)

| Service | Container Name | Port | Profile | Description |
|---------|---------------|------|---------|-------------|
| MinIO | edustream-minio | 9000, 9001 | `storage`, `full` | S3-compatible object storage |
| Celery Worker | edustream-celery-worker | - | `workers`, `full` | Background task processor |
| Celery Beat | edustream-celery-beat | - | `workers`, `full` | Periodic task scheduler |

### Port Summary

```
localhost:3000  → Frontend (Next.js)
localhost:8000  → Backend API (FastAPI)
localhost:8000/docs → Swagger API Documentation
localhost:5432  → PostgreSQL
localhost:6379  → Redis
localhost:9000  → MinIO API (optional)
localhost:9001  → MinIO Console (optional)
```

---

## Environment Variables

### Required Variables

These have sensible defaults for local development:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_DB` | Database name | `authapp` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `SECRET_KEY` | JWT signing key | Must set in production |

### MinIO Variables (for `--profile storage`)

| Variable | Description | Default |
|----------|-------------|---------|
| `MINIO_ROOT_USER` | MinIO admin username | `minioadmin` |
| `MINIO_ROOT_PASSWORD` | MinIO admin password | `minioadmin` |

### Optional Feature Variables

| Variable | Description | Feature |
|----------|-------------|---------|
| `STRIPE_SECRET_KEY` | Stripe API key | Payments |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | Payments |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Social login |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | Social login |
| `BREVO_API_KEY` | Brevo API key | Email notifications |
| `ZOOM_CLIENT_ID` | Zoom API client ID | Zoom integration |
| `SENTRY_DSN` | Sentry DSN | Error monitoring |

See `.env.example` for the complete list with descriptions.

---

## Production Deployment

### Build Production Images

```bash
# Build with production target and API URL
docker compose build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  backend frontend

# Or build each service explicitly
docker compose build backend --target production
docker compose build frontend --target production
```

### Production Compose Override

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      target: production
    restart: always

  frontend:
    build:
      target: production
      args:
        NEXT_PUBLIC_API_URL: https://api.yourdomain.com
    restart: always

  db:
    restart: always

  redis:
    restart: always
```

Run with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set strong `MINIO_ROOT_PASSWORD`
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Set `NEXT_PUBLIC_API_URL` to your API domain
- [ ] Configure Stripe keys for payments
- [ ] Configure email service (Brevo)
- [ ] Set up SSL/TLS termination (nginx/traefik)
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up monitoring (Sentry DSN)

---

## Troubleshooting

### Common Issues

#### Backend won't start / "Connection refused"

```bash
# Check if database is ready
docker compose logs db
docker compose exec db pg_isready -U postgres

# Wait for health check, then restart backend
docker compose restart backend
```

#### Frontend shows "Failed to fetch" errors

```bash
# Verify backend is healthy
curl http://localhost:8000/health

# Check backend logs
docker compose logs backend

# Verify NEXT_PUBLIC_API_URL is correct
docker compose exec frontend printenv | grep API
```

#### MinIO not starting

```bash
# Ensure you're using the storage profile
docker compose --profile storage up -d

# Check MinIO logs
docker compose logs minio
```

#### Celery tasks not running

```bash
# Ensure you're using the workers profile
docker compose --profile workers up -d

# Check worker logs
docker compose logs celery-worker
docker compose logs celery-beat
```

#### Port already in use

```bash
# Find what's using the port
lsof -i :8000
# or on Windows
netstat -ano | findstr :8000

# Stop the conflicting process or change port in docker-compose.yml
```

#### Out of disk space

```bash
# Clean up Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune
```

### Reset Everything

```bash
# Nuclear option: stop everything, remove volumes, rebuild
docker compose down -v
docker system prune -f
docker compose --profile full up -d --build
```

### Debug Mode

```bash
# Run backend with more verbose logging
docker compose exec backend bash
LOG_LEVEL=DEBUG uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Check environment variables
docker compose exec backend printenv | sort
```

### Health Check Status

```bash
# View detailed health status
docker compose ps

# Expected healthy output:
# NAME                  STATUS                   PORTS
# edustream-db          running (healthy)        0.0.0.0:5432->5432/tcp
# edustream-redis       running (healthy)        0.0.0.0:6379->6379/tcp
# edustream-backend     running (healthy)        0.0.0.0:8000->8000/tcp
# edustream-frontend    running                  0.0.0.0:3000->3000/tcp
```

---

## Architecture

### Container Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Frontend │    │ Backend  │    │   DB     │    │  Redis   │  │
│  │  :3000   │───▶│  :8000   │───▶│  :5432   │    │  :6379   │  │
│  └──────────┘    └────┬─────┘    └──────────┘    └────▲─────┘  │
│                       │                               │         │
│                       │         ┌──────────┐          │         │
│                       └────────▶│  MinIO   │          │         │
│                       │         │:9000/9001│          │         │
│                       │         └──────────┘          │         │
│                       │                               │         │
│                       │  ┌────────────┐  ┌─────────┐  │         │
│                       └─▶│   Celery   │──│  Celery │──┘         │
│                          │   Worker   │  │   Beat  │            │
│                          └────────────┘  └─────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Browser/API   │
                    │     Client      │
                    └─────────────────┘
```

### File Structure

```
.
├── docker-compose.yml       # Main compose configuration
├── docker-compose.test.yml  # Test configuration
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── Makefile                 # Command shortcuts
├── DOCKER.md                # This file
│
├── backend/
│   ├── Dockerfile           # Multi-stage build (development, production)
│   ├── Dockerfile.test      # Test-specific build
│   ├── .dockerignore        # Excluded files
│   ├── main.py              # FastAPI application entry
│   ├── requirements.txt     # Python dependencies
│   └── ...
│
├── frontend/
│   ├── Dockerfile           # Multi-stage build (development, production)
│   ├── Dockerfile.test      # Test-specific build
│   ├── Dockerfile.playwright # E2E testing
│   ├── .dockerignore        # Excluded files
│   ├── package.json         # Node dependencies
│   └── ...
│
└── database/
    └── init.sql             # Database schema initialization
```

### Dockerfile Targets

**Backend (`backend/Dockerfile`):**
- `development` - Hot-reload with uvicorn --reload
- `production` - Optimized with 4 workers, non-root user

**Frontend (`frontend/Dockerfile`):**
- `development` - Hot-reload with next dev
- `production` - Standalone build, minimal image, non-root user

```bash
# Build specific target
docker compose build backend --target production
docker compose build frontend --target production
```
