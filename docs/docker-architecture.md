# Docker Architecture - News Trading Ideas Platform

**Version:** 1.0.0
**Date:** 2025-10-22
**Status:** Architecture Design
**Architect:** System Architecture Designer

---

## Executive Summary

This document defines the Docker-based deployment architecture for the News Trading Ideas MVP platform. The design prioritizes simplicity, cost efficiency, and ease of deployment while maintaining clear upgrade paths for production scaling.

**Key Design Principles:**
- Single container deployment for MVP
- Multi-stage builds for optimized image size
- Environment-based configuration
- Volume persistence for data and logs
- One-command deployment experience

---

## 1. Container Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER CONTAINER                                │
│                     news-trading-ideas:latest                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               APPLICATION LAYER (Python 3.11+)                  │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  FastAPI Web Server (Uvicorn)                            │  │    │
│  │  │  • REST API endpoints (/api/v1/*)                        │  │    │
│  │  │  • Static file serving (frontend build)                  │  │    │
│  │  │  • WebSocket connections (optional)                      │  │    │
│  │  │  • Health check endpoint (/health)                       │  │    │
│  │  │  Port: 8000 (exposed externally)                         │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                                                                 │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Background Services                                      │  │    │
│  │  │  • APScheduler (feed ingestion, clustering, ideas)       │  │    │
│  │  │  • OpenAI API client (embeddings, clustering, GPT-4)     │  │    │
│  │  │  • RSS parser (feedparser + httpx)                       │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               FRONTEND LAYER (React + Vite)                     │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  /app/frontend/dist/ (Static Build)                            │    │
│  │  • index.html (SPA entry point)                                │    │
│  │  • assets/*.js (bundled JavaScript)                            │    │
│  │  • assets/*.css (Tailwind CSS)                                 │    │
│  │  Served by FastAPI at: /                                       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               DATA LAYER (SQLite)                               │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  /data/app.db (SQLite database file)                           │    │
│  │  • WAL mode enabled (concurrent reads/writes)                  │    │
│  │  • FTS5 full-text search                                       │    │
│  │  • Initialized on first startup                                │    │
│  │  Volume mounted: ./data:/data (persistence)                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               LOGGING LAYER                                     │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  /app/logs/ (Structured JSON logs)                             │    │
│  │  • app.log (application logs)                                  │    │
│  │  • ingestion.log (RSS feed logs)                               │    │
│  │  • api.log (API request/response logs)                         │    │
│  │  Volume mounted: ./logs:/app/logs (persistence)                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               │ Port 8000:8000
                               ▼
                    ┌─────────────────────┐
                    │   Host Machine      │
                    │   Browser Access    │
                    │   http://localhost  │
                    └─────────────────────┘
```

---

## 2. Multi-Stage Dockerfile Strategy

The Dockerfile uses a three-stage build process to optimize image size and security:

### Stage 1: Frontend Build (Node.js)
- Base image: `node:20-alpine`
- Install frontend dependencies
- Build React app with Vite
- Output: Static files in `/dist`

### Stage 2: Python Dependencies
- Base image: `python:3.11-slim`
- Install Python dependencies via Poetry
- No development dependencies
- Output: Virtual environment

### Stage 3: Runtime Image
- Base image: `python:3.11-slim`
- Copy frontend build from Stage 1
- Copy Python dependencies from Stage 2
- Copy application code
- Configure runtime environment
- Output: Optimized production image

**Benefits:**
- Reduced image size (no build tools in final image)
- Faster deployment (cached layers)
- Improved security (minimal attack surface)
- Reproducible builds

---

## 3. Port Mapping Strategy

### External Port Exposure

```
Host Machine Port 8000 → Container Port 8000
    ↓
FastAPI Application Server
    ↓
    ├─→ API Endpoints (/api/v1/*)
    ├─→ Frontend Static Files (/)
    ├─→ Health Check (/health)
    └─→ API Documentation (/docs)
```

### Port Configuration Details

| Port | Type | Purpose | Exposed |
|------|------|---------|---------|
| 8000 | TCP | HTTP (API + Frontend) | Yes (host:8000) |
| N/A | N/A | SQLite (file-based) | N/A |
| N/A | N/A | APScheduler (in-process) | N/A |

**Rationale for Single Port:**
- Simplifies deployment (no reverse proxy needed for MVP)
- FastAPI serves both API and static files efficiently
- Reduces configuration complexity
- Easy to add Nginx/Caddy later if needed

### Future Port Expansion (Post-MVP)

```
┌──────────────────────────────────────┐
│  Caddy Reverse Proxy                 │
│  Port 80 (HTTP) → 443 (HTTPS)        │
└────────────┬─────────────────────────┘
             │
             ├─→ /api/* → Backend:8000
             ├─→ /* → Frontend:8000
             └─→ /ws → WebSocket:8000
```

---

## 4. Volume Mount Strategy

### Data Persistence Architecture

```
Host Filesystem           Container Filesystem
─────────────────         ───────────────────

./data/                   /data/
├── app.db        ←→      ├── app.db (SQLite database)
├── app.db-shm    ←→      ├── app.db-shm (WAL shared memory)
├── app.db-wal    ←→      └── app.db-wal (Write-ahead log)
└── backups/
    └── *.db.gz

./logs/                   /app/logs/
├── app.log       ←→      ├── app.log (application logs)
├── ingestion.log ←→      ├── ingestion.log (RSS feed logs)
├── api.log       ←→      ├── api.log (API logs)
└── ai.log        ←→      └── ai.log (OpenAI API logs)

.env              ←→      /app/.env (environment variables)
```

### Volume Mount Configuration

| Host Path | Container Path | Purpose | Mode |
|-----------|---------------|---------|------|
| `./data` | `/data` | SQLite database persistence | rw |
| `./logs` | `/app/logs` | Application logs | rw |
| `./.env` | `/app/.env` | Environment configuration | ro |

### Directory Initialization

The container startup script creates necessary directories:

```bash
#!/bin/bash
# entrypoint.sh

# Create data directory if it doesn't exist
mkdir -p /data

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Initialize database if it doesn't exist
if [ ! -f /data/app.db ]; then
    echo "Initializing database..."
    python -m app.db.init_db
fi

# Start application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Backup Strategy

**Automated Backups:**
- Daily backups at 2 AM UTC
- Retention: 30 days
- Location: `./data/backups/`
- Format: `backup_YYYYMMDD_HHMMSS.db.gz`

**Backup Script (runs as cron job in container):**
```bash
sqlite3 /data/app.db ".backup /data/backups/backup_$(date +%Y%m%d_%H%M%S).db"
gzip /data/backups/backup_*.db
find /data/backups -name "*.db.gz" -mtime +30 -delete
```

---

## 5. Environment Configuration

### Environment Variables (.env file)

```bash
# Application Configuration
APP_NAME=news-trading-ideas
APP_ENV=production
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///data/app.db
DATABASE_WAL_MODE=true
DATABASE_CACHE_SIZE=64000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=false

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-api-key-here
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
OPENAI_MODEL_CLUSTERING=gpt-4o-mini
OPENAI_MODEL_IDEAS=gpt-4o
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30

# RSS Feed Configuration
FEED_REFRESH_INTERVAL=300
FEED_MAX_CONCURRENT=5
FEED_TIMEOUT=30

# AI Processing Configuration
CLUSTERING_BATCH_SIZE=50
CLUSTERING_SIMILARITY_THRESHOLD=0.75
IDEAS_TOP_N_EVENTS=10
IDEAS_MIN_CONFIDENCE=0.6

# Security Configuration
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:5173
SECRET_KEY=your-secret-key-change-in-production

# Monitoring Configuration
ENABLE_METRICS=true
HEALTH_CHECK_INTERVAL=60
```

### Environment Variables Validation

The application validates required environment variables on startup:

```python
# app/config.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Required
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')

    # Optional with defaults
    database_url: str = Field('sqlite:///data/app.db', env='DATABASE_URL')
    api_port: int = Field(8000, env='API_PORT')
    log_level: str = Field('INFO', env='LOG_LEVEL')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
```

---

## 6. Container Initialization Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Container Start                                          │
│    docker-compose up -d                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Entrypoint Script (entrypoint.sh)                        │
│    • Validate environment variables                         │
│    • Create directories (/data, /logs)                      │
│    • Set permissions (if needed)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Database Initialization                                  │
│    • Check if /data/app.db exists                           │
│    • If not: Run schema.sql to create tables                │
│    • Enable WAL mode, set pragmas                           │
│    • Create indexes                                         │
│    • Insert default system_metadata                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Application Bootstrap                                    │
│    • Load configuration from .env                           │
│    • Initialize logging                                     │
│    • Connect to database                                    │
│    • Validate OpenAI API key                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. FastAPI Server Startup                                   │
│    • Initialize FastAPI app                                 │
│    • Mount static files from /app/frontend/dist            │
│    • Register API routes                                    │
│    • Start APScheduler background jobs                      │
│    • Bind to 0.0.0.0:8000                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Background Services Start                                │
│    • RSS feed ingestion scheduler (every 5-15 min)          │
│    • Article clustering job (triggered by new articles)     │
│    • Trading idea generation (for top 10 events)            │
│    • Database maintenance (daily)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Ready for Requests                                       │
│    • Health check: http://localhost:8000/health             │
│    • Frontend: http://localhost:8000/                       │
│    • API docs: http://localhost:8000/docs                   │
└─────────────────────────────────────────────────────────────┘
```

### Startup Time Expectations

| Phase | Expected Duration | Notes |
|-------|------------------|-------|
| Container start | 1-2 seconds | Image pull time excluded |
| Database init (first run) | 2-3 seconds | Only on first startup |
| Database init (subsequent) | <100ms | Existing DB validation |
| Application bootstrap | 1-2 seconds | Config loading, connections |
| FastAPI server start | 1-2 seconds | Route registration |
| Background jobs init | <1 second | Scheduler setup |
| **Total (first run)** | **6-10 seconds** | Initial deployment |
| **Total (restart)** | **3-5 seconds** | Hot restart |

---

## 7. Health Checks and Monitoring

### Health Check Endpoint

```python
# app/api/routes/health.py
@router.get("/health")
async def health_check():
    """
    Comprehensive health check for Docker health monitoring
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": await check_database(),
            "openai_api": await check_openai(),
            "scheduler": await check_scheduler(),
            "disk_space": await check_disk_space()
        }
    }

    if any(c["status"] != "up" for c in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status
```

### Docker Health Check Configuration

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Monitoring Metrics

**Application Metrics (exposed at `/metrics`):**
- Article ingestion rate (articles/hour)
- API request count and latency
- OpenAI API usage and costs
- Database size and query performance
- Active background jobs

**System Metrics (Docker stats):**
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

---

## 8. Build and Deployment Commands

### Development Build

```bash
# Build development image
docker build -t news-trading-ideas:dev \
  --target development \
  --build-arg NODE_ENV=development \
  .

# Run with hot reload
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd)/backend:/app \
  -v $(pwd)/data:/data \
  -v $(pwd)/.env:/app/.env \
  news-trading-ideas:dev
```

### Production Build

```bash
# Build production image
docker build -t news-trading-ideas:latest \
  --build-arg NODE_ENV=production \
  .

# Verify image size
docker images news-trading-ideas:latest

# Expected size: ~300-400MB (Python + compiled frontend)
```

### Multi-Architecture Build (Optional)

```bash
# Build for multiple platforms (ARM + AMD64)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t news-trading-ideas:latest \
  --push \
  .
```

### Run Production Container

```bash
# Run with docker-compose (recommended)
docker-compose up -d

# Or run standalone
docker run -d \
  --name news-trading-ideas \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  --restart unless-stopped \
  news-trading-ideas:latest
```

### Container Management Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Execute commands in running container
docker-compose exec app python -m app.cli.manage --help

# Database backup
docker-compose exec app python -m app.cli.backup --output /data/backups

# Database migration
docker-compose exec app alembic upgrade head
```

---

## 9. Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Container fails to start

**Symptoms:**
```
Error: No such file or directory: '.env'
```

**Solution:**
```bash
# Create .env file from template
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
nano .env
```

#### Issue 2: Database locked errors

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Check WAL mode is enabled
docker-compose exec app sqlite3 /data/app.db "PRAGMA journal_mode;"
# Should return: wal

# If not, enable WAL mode
docker-compose exec app sqlite3 /data/app.db "PRAGMA journal_mode=WAL;"
```

#### Issue 3: Frontend not loading

**Symptoms:**
- API works at `/docs`
- Frontend returns 404 at `/`

**Solution:**
```bash
# Verify frontend build exists
docker-compose exec app ls -la /app/frontend/dist

# If missing, rebuild container
docker-compose up -d --build
```

#### Issue 4: High memory usage

**Symptoms:**
- Container uses >2GB RAM

**Solution:**
```bash
# Check for memory leaks in logs
docker-compose logs app | grep -i "memory"

# Restart container to free memory
docker-compose restart app

# Set memory limits in docker-compose.yml
```

#### Issue 5: OpenAI API rate limits

**Symptoms:**
```
openai.error.RateLimitError: Rate limit exceeded
```

**Solution:**
```bash
# Check current API usage
docker-compose logs app | grep -i "rate limit"

# Reduce batch sizes in .env
CLUSTERING_BATCH_SIZE=25  # down from 50
IDEAS_TOP_N_EVENTS=5      # down from 10

# Restart to apply changes
docker-compose restart app
```

---

## 10. Security Considerations

### Container Security Best Practices

**1. Non-Root User**
```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser
```

**2. Read-Only Root Filesystem (Optional)**
```yaml
# docker-compose.yml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
```

**3. Resource Limits**
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**4. Secret Management**
```bash
# Use Docker secrets instead of .env file
echo "sk-proj-your-key" | docker secret create openai_api_key -

# Reference in docker-compose.yml
secrets:
  - openai_api_key
```

**5. Network Isolation**
```yaml
# docker-compose.yml
networks:
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge
```

---

## 11. Upgrade Path to Production

### Phase 1: MVP (Current Design)
```
Single Docker container
    ├── FastAPI + Frontend
    ├── SQLite database
    └── APScheduler
```

### Phase 2: Separated Services
```
Docker Compose (3 services)
    ├── Backend (FastAPI + APScheduler)
    ├── Frontend (Nginx serving static files)
    └── Database (PostgreSQL container)
```

### Phase 3: Microservices
```
Kubernetes Deployment
    ├── API Service (3 replicas)
    ├── Ingestion Service (2 replicas)
    ├── AI Processing Service (1 replica)
    ├── Frontend Service (2 replicas)
    ├── PostgreSQL (StatefulSet)
    ├── Redis (Caching + Task Queue)
    └── Prometheus + Grafana (Monitoring)
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Single Container for MVP

**Context:** Need to minimize deployment complexity for MVP while maintaining upgrade paths.

**Decision:** Deploy backend, frontend, and database in a single Docker container.

**Rationale:**
- Fastest time to deployment (one command: `docker-compose up`)
- Minimal infrastructure costs (single VPS instance)
- Simplified networking (no service discovery needed)
- Easy local development (matches production closely)
- SQLite is file-based (no separate DB container needed)

**Consequences:**
- **Positive:** Ultra-simple deployment, low cost, easy debugging
- **Negative:** Limited horizontal scaling, single point of failure
- **Mitigation:** Clear upgrade path documented for Phase 2+

**Status:** Accepted for MVP

---

### ADR-002: Multi-Stage Docker Build

**Context:** Need to optimize image size and build time.

**Decision:** Use multi-stage build with separate Node.js and Python stages.

**Rationale:**
- Frontend build requires Node.js (100+ MB)
- Runtime only needs Python + compiled frontend
- Build tools not needed in final image
- Reduces attack surface (fewer dependencies)
- Faster deployments (smaller images)

**Consequences:**
- **Positive:** 50-60% smaller final image, faster pulls, more secure
- **Negative:** Slightly more complex Dockerfile
- **Mitigation:** Well-documented build stages with comments

**Status:** Accepted

---

### ADR-003: Volume Mounts for Data Persistence

**Context:** Need to persist database and logs across container restarts.

**Decision:** Use bind mounts for `./data` and `./logs` directories.

**Rationale:**
- Easy backup (copy host directory)
- Easy inspection (view logs without exec)
- Portable (move to different hosts easily)
- Works with Docker Desktop on all platforms

**Consequences:**
- **Positive:** Simple backups, easy debugging, portable data
- **Negative:** Tied to host filesystem (not cloud-native)
- **Mitigation:** Plan migration to Docker volumes for Phase 2

**Status:** Accepted for MVP

---

## Next Steps

1. **Implement Dockerfile** (backend and frontend multi-stage build)
2. **Create docker-compose.yml** (service definition, volumes, networks)
3. **Write entrypoint.sh** (initialization script)
4. **Create .env.example** (template for required variables)
5. **Test deployment** (local development and production builds)
6. **Document deployment** (README with step-by-step instructions)
7. **Store architecture in memory** (for swarm coordination)

---

**Document Control:**
- **Version**: 1.0.0
- **Last Updated**: 2025-10-22
- **Status**: Architecture Design Complete
- **Next Review**: After implementation testing
