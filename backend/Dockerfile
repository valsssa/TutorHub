# =============================================================================
# EduStream Backend Dockerfile
# Multi-stage build: development (hot-reload) and production (optimized)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base - Common setup for all stages
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 2: Dependencies - Install Python packages (cached layer)
# -----------------------------------------------------------------------------
FROM base AS deps

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Development - Hot-reload for local development
# -----------------------------------------------------------------------------
FROM deps AS development

WORKDIR /app

# Copy application code (volumes override this in dev)
COPY backend/ ./backend/
COPY database/ ./database/

WORKDIR /app/backend

EXPOSE 8000

# Development server with hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Stage 4: Production - Optimized for deployment
# -----------------------------------------------------------------------------
FROM base AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# Copy application code with correct ownership
COPY --chown=appuser:appuser backend/ ./backend/
COPY --chown=appuser:appuser database/ ./database/

WORKDIR /app/backend

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production server with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
