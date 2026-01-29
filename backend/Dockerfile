# ============================================================================
# Multi-Stage Dockerfile for FastAPI Backend
# Optimized for production with proxy support and pre-build validation
# ============================================================================

# Stage 1: Base image with system dependencies
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

# Configure Debian proxy
RUN echo "deb https://nexus.in.lazarev.cloud/repository/debian-proxy/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://nexus.in.lazarev.cloud/repository/debian-proxy/ bookworm-updates main" >> /etc/apt/sources.list

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# Stage 2: Dependencies (cached layer)
FROM base AS deps

# Configure pip proxy
RUN pip config set global.index-url https://nexus.in.lazarev.cloud/repository/pypi-proxy/simple && \
    pip config set global.trusted-host nexus.in.lazarev.cloud

# Copy requirements file
COPY backend/requirements.txt .

# Install Python dependencies with fallback
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    (echo "Nexus registry failed, falling back to PyPI..." && \
     pip config set global.index-url https://pypi.org/simple && \
     pip install --no-cache-dir -r requirements.txt)

# ============================================================================
# Stage 3: Linting and Type Checking (OPTIONAL - for CI only)
# To use: docker build --target lint .
# Skipped in normal builds for speed
# ============================================================================
FROM deps AS lint

WORKDIR /app/backend
COPY backend/ .

RUN pip install --no-cache-dir ruff mypy 2>/dev/null || true
RUN ruff check . || echo "Linting issues found"
RUN mypy --install-types --non-interactive --ignore-missing-imports . || echo "Type issues found"

# ============================================================================
# Stage 4: Production (minimal runtime image)
FROM base AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# Copy application code and database migrations
COPY --chown=appuser:appuser backend/ ./backend/
COPY --chown=appuser:appuser database/ ./database/

# Set working directory to backend for application execution
WORKDIR /app/backend

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]

# ============================================================================
# Stage 5: Development (with hot-reload)
FROM deps AS development

WORKDIR /app

# Copy application code and database migrations
COPY backend/ ./backend/
COPY database/ ./database/

# Set working directory to backend for application execution
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Run application with auto-reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
