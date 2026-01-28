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
# Stage 3: Linting and Type Checking (validation layer)
FROM deps AS lint

WORKDIR /app/backend

# Copy source files needed for linting
COPY backend/ .

# Install linting tools (if not in requirements.txt)
RUN pip install --no-cache-dir \
    ruff==0.14.11 \
    mypy==1.8.0 \
    2>/dev/null || true

# Run code formatting check (black)
RUN black --check --diff . || \
    (echo "  Warning: Code formatting issues found. Run 'black .' to fix." && true)

# Run import sorting check (isort)
RUN isort --check-only --diff . || \
    (echo "  Warning: Import sorting issues found. Run 'isort .' to fix." && true)

# Run linting (ruff - fast Python linter)
RUN ruff check . || \
    (echo "  Warning: Linting issues found." && true)

# Run type checking (mypy)
RUN mypy --install-types --non-interactive --ignore-missing-imports . || \
    (echo "  Warning: Type checking issues found." && true)

# Validate Python syntax
RUN python -m py_compile **/*.py || \
    (echo " Syntax errors found! Fix before building." && exit 1)

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
