# Docker Configuration Updated

**Date:** October 22, 2025
**Status:** ✅ Complete

## Changes Made

### 1. Updated Dockerfile

**Key Changes:**
- ✅ Fixed paths to use `src/frontend/` and `src/backend/`
- ✅ Updated to Node 20 (from 18)
- ✅ Added Poetry for Python dependency management
- ✅ Frontend build output: `dist` (Vite default)
- ✅ Backend served from `/app/app/main.py`
- ✅ Static files served from `/app/static/`
- ✅ Database initialization in CMD
- ✅ Non-root user (appuser:1000)

**Build Stages:**
1. **frontend-build**: Node 20 Alpine → builds React app with Vite
2. **backend-deps**: Python 3.11 → installs Poetry dependencies
3. **production**: Final image with both backend + static frontend

### 2. Updated docker-compose.yml

**Environment Variables Updated:**
```yaml
# OLD (GPT-4):
OPENAI_MODEL_CLUSTERING: gpt-4o-mini
OPENAI_MODEL_IDEAS: gpt-4o

# NEW (GPT-5):
OPENAI_CLUSTERING_MODEL: gpt-5-mini
OPENAI_IDEAS_MODEL: gpt-5
ENABLE_WEB_SEARCH: true
```

**New Variables Added:**
- `OPENAI_BASE_URL` - API endpoint
- `ENABLE_WEB_SEARCH` - Web search tool toggle
- `AI_PROCESS_INTERVAL` - Background job interval
- `MAX_DAILY_OPENAI_COST` - Cost control
- `ENABLE_CORS` - CORS toggle

**Database Path Fixed:**
- Old: `sqlite:///data/app.db`
- New: `sqlite+aiosqlite:///./data/news_trading.db`

### 3. Created .env.example

Complete environment variable template with:
- All GPT-5 model configurations
- Web search settings
- Cost controls
- Detailed comments
- Default values

### 4. Created docker-compose.dev.yml

For local development with:
- Hot reload for backend (uvicorn --reload)
- Hot reload for frontend (Vite dev server)
- Volume mounts for live code changes
- Debug logging enabled

## Project Structure

```
news-trading-ideas/
├── Dockerfile                    # ✅ UPDATED - Production multi-stage build
├── docker-compose.yml            # ✅ UPDATED - GPT-5 config
├── docker-compose.dev.yml        # ✅ NEW - Development config
├── .env.example                  # ✅ NEW - Environment template
├── .env                          # User creates this
├── src/
│   ├── backend/                  # ✅ Dockerfile references this
│   │   ├── app/
│   │   ├── pyproject.toml
│   │   └── poetry.lock
│   └── frontend/                 # ✅ Dockerfile references this
│       ├── package.json
│       └── src/
├── architecture/
│   └── database-schema.sql       # ✅ Copied to container
├── data/                         # ✅ Volume mount
├── logs/                         # ✅ Volume mount
└── docs/
```

## Usage

### Production Build

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add OPENAI_API_KEY

# 2. Build and run
docker-compose up -d

# 3. Check health
curl http://localhost:8000/health

# 4. Access UI
open http://localhost:8000
```

### Development Mode

```bash
# 1. Use dev compose file
docker-compose -f docker-compose.dev.yml up

# Backend: http://localhost:8000 (hot reload)
# Frontend: http://localhost:5173 (hot reload)
```

## Build Process

**Stage 1: Frontend (Node 20)**
```dockerfile
COPY src/frontend/package*.json ./
npm ci
COPY src/frontend/ ./
npm run build  # → dist/ directory
```

**Stage 2: Backend Dependencies (Poetry)**
```dockerfile
COPY src/backend/pyproject.toml src/backend/poetry.lock ./
poetry install --no-dev
```

**Stage 3: Final Image**
```dockerfile
COPY src/backend/app ./app
COPY --from=frontend-build /app/frontend/dist ./static
COPY architecture/database-schema.sql ./

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Container Startup Sequence

1. **Database Initialization:**
   - Create `/data` directory
   - Initialize SQLite database
   - Enable WAL mode

2. **FastAPI Server:**
   - Load environment variables
   - Connect to database
   - Mount static frontend at `/`
   - Start background schedulers
   - Listen on port 8000

3. **Health Check:**
   - Container marked healthy after successful `/health` response
   - Runs every 30 seconds

## Environment Variables

### Required
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional (with defaults)
- `OPENAI_CLUSTERING_MODEL=gpt-5-mini`
- `OPENAI_IDEAS_MODEL=gpt-5`
- `ENABLE_WEB_SEARCH=true`
- `MAX_DAILY_OPENAI_COST=5.0`
- See `.env.example` for complete list

## Volumes

```yaml
volumes:
  - ./data:/data                    # SQLite database
  - ./logs:/app/logs                # Application logs
  - ./.env:/app/.env:ro             # Environment (read-only)
```

## Ports

- **8000** - HTTP (UI + API)
  - UI: http://localhost:8000/
  - API: http://localhost:8000/api/v1/
  - Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health

## Testing

```bash
# Build image
docker build -t news-trading-ideas:test .

# Run container
docker run -d \
  --name test-container \
  -p 8000:8000 \
  --env-file .env \
  news-trading-ideas:test

# Check logs
docker logs test-container

# Verify GPT-5 usage
docker logs test-container | grep "gpt-5"

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/feeds

# Cleanup
docker stop test-container && docker rm test-container
```

## Troubleshooting

### Issue: Build fails on frontend stage
```bash
# Check package.json exists
ls -la src/frontend/package.json

# Verify Node version
docker run --rm node:20-alpine node --version
```

### Issue: Build fails on backend stage
```bash
# Check pyproject.toml exists
ls -la src/backend/pyproject.toml

# Verify Poetry can read it
cd src/backend && poetry check
```

### Issue: Container starts but API unreachable
```bash
# Check container logs
docker logs news-trading-ideas

# Verify port binding
docker port news-trading-ideas

# Check health
docker exec news-trading-ideas curl http://localhost:8000/health
```

### Issue: Database errors
```bash
# Check database file exists
docker exec news-trading-ideas ls -la /data/

# Verify WAL mode
docker exec news-trading-ideas sqlite3 /data/news_trading.db "PRAGMA journal_mode;"
```

## Next Steps

1. ✅ Docker files updated
2. ✅ Environment template created
3. ⏳ Build Docker image
4. ⏳ Test container locally
5. ⏳ Deploy to production

## Files Modified

- ✅ `/Dockerfile` - Updated paths, added Poetry
- ✅ `/docker-compose.yml` - GPT-5 config
- ✅ `/.env.example` - Complete template
- ✅ `/docker-compose.dev.yml` - Dev config (new)
- ✅ `/docs/DOCKER-UPDATED.md` - This document

---

**Status:** Ready for build and test!
