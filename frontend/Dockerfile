# ============================================================================
# Multi-Stage Dockerfile for Next.js Frontend
# Optimized for production with proxy support and pre-build validation
# ============================================================================

# Stage 1: Dependencies (cached layer)
FROM node:20-alpine AS deps

WORKDIR /app

# Configure npm proxy with fallback
RUN npm config set registry https://registry.npmjs.org && \
    npm config set strict-ssl false

# Copy package files (including lock file for faster, deterministic installs)
COPY package.json package-lock.json ./

# Install dependencies using npm ci for faster, reproducible builds
RUN npm ci --prefer-offline 2>/dev/null || \
    (echo "Registry failed, falling back to official npm..." && \
     npm config set registry https://registry.npmjs.org/ && \
     npm cache clean --force && \
     npm ci)

# ============================================================================
# Stage 2: Linting and Type Checking (validation layer)
FROM node:20-alpine AS lint

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source files needed for linting and type checking
COPY . .

# Run linting (fails build if errors found)
RUN npm run lint || (echo "❌ Linting failed! Fix errors before building." && exit 1)

# Run type checking (fails build if errors found)
RUN npm run type-check || (echo "❌ Type checking failed! Fix type errors before building." && exit 1)

# ============================================================================
# Stage 3: Builder (build stage)
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# Build arguments for Next.js environment variables
ARG NEXT_PUBLIC_API_URL=https://api.valsa.solutions
ARG NEXT_PUBLIC_LOG_LEVEL=INFO

# Set build environment
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_LOG_LEVEL=$NEXT_PUBLIC_LOG_LEVEL

# Build the application (will create .next/standalone if configured)
RUN npm run build && \
    echo "✅ Build completed successfully!"

# ============================================================================
# Stage 4: Runner (production stage - using standard Next.js start)
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy package files for npm start
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.js ./next.config.js

# Copy built Next.js application
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start application
CMD ["npm", "start"]
