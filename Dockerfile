# Multi-stage Dockerfile for News Trading Ideas MVP
# Builds frontend with Vite and backend with FastAPI + SQLite
# Final image exposes port 8000 for web interface

# Stage 1: Frontend Build (React + Vite + TypeScript)
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY src/frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY src/frontend/ ./

# Build production frontend
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Backend Dependencies (Python + Poetry)
FROM python:3.11-slim AS backend-deps

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy backend dependency files
COPY src/backend/pyproject.toml src/backend/poetry.lock ./

# Install dependencies (no dev packages)
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Stage 3: Final Production Image
FROM python:3.11-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from backend-deps stage
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy backend code
COPY src/backend/app ./app
COPY src/backend/alembic ./alembic
COPY src/backend/alembic.ini ./
COPY src/backend/scripts ./scripts

# Copy frontend build from stage 1 (served as static files by FastAPI)
COPY --from=frontend-build /app/frontend/dist ./static

# Copy database schema
COPY architecture/database-schema.sql ./database-schema.sql

# Create necessary directories
RUN mkdir -p /data /app/logs /backups

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data /backups

# Create directory for database
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    PYTHONPATH=/app

# Copy and use entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
