# Deployment Guide - News Trading Ideas Platform

**Version:** 1.0.0
**Date:** 2025-10-22
**Status:** Implementation Ready

---

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd news-trading-ideas

# 2. Create .env file
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# 3. Create data directories
mkdir -p data logs

# 4. Start with Docker Compose
docker-compose up -d

# 5. Verify deployment
curl http://localhost:8000/health

# 6. Access application
# Frontend: http://localhost:8000/
# API Docs: http://localhost:8000/docs
```

---

## Prerequisites

### Required Software
- Docker 24.0+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- 2GB free disk space
- OpenAI API key ([Get API Key](https://platform.openai.com/api-keys))

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 core | 2 cores |
| RAM | 512 MB | 1 GB |
| Disk | 1 GB | 5 GB |
| Network | 10 Mbps | 50 Mbps |

---

## Detailed Deployment Steps

### Step 1: Environment Configuration

Create `.env` file with required settings:

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings:**
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
SECRET_KEY=your-random-secret-key
```

**Generate secret key:**
```bash
openssl rand -hex 32
```

### Step 2: Directory Structure Setup

Create necessary directories:

```bash
# Data directory (SQLite database)
mkdir -p data/backups

# Logs directory
mkdir -p logs

# Docker scripts directory
mkdir -p docker

# Set permissions (Linux/macOS)
chmod 755 data logs
```

### Step 3: Build Docker Image

```bash
# Build production image
docker-compose build

# Verify image created
docker images | grep news-trading-ideas
```

Expected output:
```
news-trading-ideas  latest  abc123def456  2 minutes ago  350MB
```

### Step 4: Start Services

```bash
# Start in background (detached mode)
docker-compose up -d

# View startup logs
docker-compose logs -f

# Wait for healthy status (15-30 seconds)
docker-compose ps
```

Expected output:
```
NAME                   STATUS         PORTS
news-trading-ideas     Up (healthy)   0.0.0.0:8000->8000/tcp
```

### Step 5: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": {"status": "up"},
#     "openai_api": {"status": "up"},
#     "scheduler": {"status": "running"}
#   }
# }

# Test API documentation
curl http://localhost:8000/docs
# Should return HTML

# Test frontend
curl http://localhost:8000/
# Should return HTML with React app
```

---

## Post-Deployment Configuration

### Add RSS Feeds

Using API documentation interface:

1. Open http://localhost:8000/docs
2. Navigate to `/api/v1/feeds` POST endpoint
3. Add feeds with this JSON:

```json
{
  "name": "Reuters Business",
  "url": "http://feeds.reuters.com/reuters/businessNews",
  "category": "business",
  "active": true,
  "update_interval": 300
}
```

Using curl:

```bash
curl -X POST http://localhost:8000/api/v1/feeds \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bloomberg",
    "url": "https://www.bloomberg.com/feed/podcast/etf-iq.xml",
    "category": "finance",
    "active": true
  }'
```

### Trigger Initial Ingestion

```bash
# Trigger manual feed refresh
curl -X POST http://localhost:8000/api/v1/feeds/refresh

# Check ingestion progress
docker-compose logs -f app | grep "ingestion"
```

---

## Monitoring and Maintenance

### View Logs

```bash
# All logs
docker-compose logs -f

# Application logs only
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Specific log file
docker-compose exec app tail -f /app/logs/ingestion.log
```

### Check System Status

```bash
# Container status
docker-compose ps

# Resource usage
docker stats news-trading-ideas

# Database size
ls -lh data/app.db

# Disk usage
du -sh data logs
```

### Database Operations

```bash
# Backup database
docker-compose exec app sqlite3 /data/app.db ".backup /data/backups/manual_backup_$(date +%Y%m%d).db"

# Check database integrity
docker-compose exec app sqlite3 /data/app.db "PRAGMA integrity_check;"

# View database statistics
docker-compose exec app sqlite3 /data/app.db "
  SELECT
    (SELECT COUNT(*) FROM articles) as articles,
    (SELECT COUNT(*) FROM news_events) as events,
    (SELECT COUNT(*) FROM trading_ideas) as ideas;
"

# Export data
docker-compose exec app sqlite3 /data/app.db ".dump" > backup.sql
```

### Performance Monitoring

```bash
# API metrics endpoint
curl http://localhost:8000/metrics

# View OpenAI API costs (if tracking enabled)
docker-compose exec app python -m app.cli.costs --last-7-days

# Check processing stats
curl http://localhost:8000/api/v1/admin/stats
```

---

## Backup and Restore

### Automated Backups

Backups run automatically at 2 AM UTC (configured in entrypoint.sh):

```bash
# Check backup files
ls -lh data/backups/

# Should see files like:
# backup_20251022_020000.db.gz
# backup_20251021_020000.db.gz
```

### Manual Backup

```bash
# Create backup
docker-compose exec app /app/scripts/backup.sh

# Download backup to host
docker cp news-trading-ideas:/data/backups/backup_latest.db.gz ./
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore database
gunzip -c backup_20251022_020000.db.gz > data/app.db

# Restart services
docker-compose up -d

# Verify restoration
docker-compose exec app sqlite3 /data/app.db "PRAGMA integrity_check;"
```

---

## Updating the Application

### Update to Latest Version

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose up -d --build

# Run database migrations
docker-compose exec app alembic upgrade head

# Verify update
curl http://localhost:8000/health
```

### Rollback to Previous Version

```bash
# Stop services
docker-compose down

# Checkout previous version
git checkout <previous-commit-hash>

# Restore database backup
cp data/backups/backup_before_update.db data/app.db

# Rebuild and start
docker-compose up -d --build
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
1. Missing .env file → `cp .env.example .env`
2. Invalid API key → Check OPENAI_API_KEY in .env
3. Port 8000 in use → Change API_PORT in .env or stop conflicting service
4. Permission errors → `chmod 755 data logs`

### Database Locked Errors

```bash
# Check WAL mode
docker-compose exec app sqlite3 /data/app.db "PRAGMA journal_mode;"

# If not 'wal', enable it
docker-compose exec app sqlite3 /data/app.db "PRAGMA journal_mode=WAL;"

# Restart container
docker-compose restart app
```

### OpenAI API Errors

**Rate limit exceeded:**
```bash
# Reduce batch sizes in .env
CLUSTERING_BATCH_SIZE=25  # down from 50
IDEAS_TOP_N_EVENTS=5      # down from 10

# Restart
docker-compose restart app
```

**Invalid API key:**
```bash
# Verify API key format
echo $OPENAI_API_KEY  # Should start with 'sk-proj-' or 'sk-'

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Frontend Not Loading

```bash
# Verify frontend build exists
docker-compose exec app ls -la /app/frontend/dist

# If missing, rebuild
docker-compose up -d --build

# Check static file serving
curl -I http://localhost:8000/
```

### High Memory Usage

```bash
# Check current usage
docker stats news-trading-ideas

# Restart to free memory
docker-compose restart app

# Set memory limits in docker-compose.yml
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

---

## Production Deployment Checklist

- [ ] Environment configuration secured (.env not in git)
- [ ] Strong SECRET_KEY generated
- [ ] OPENAI_API_KEY configured and tested
- [ ] Data directory created with correct permissions
- [ ] Logs directory created
- [ ] Docker health checks passing
- [ ] Database initialized and validated
- [ ] RSS feeds configured
- [ ] Automated backups scheduled
- [ ] Monitoring and alerting configured
- [ ] Firewall configured (if applicable)
- [ ] SSL/TLS configured (if using reverse proxy)
- [ ] CORS origins configured correctly
- [ ] Resource limits set in docker-compose.yml
- [ ] Log rotation configured

---

## Next Steps

1. **Add RSS Feeds**: Configure your financial news sources
2. **Test Ingestion**: Verify articles are being processed
3. **Review Clusters**: Check event grouping quality
4. **Monitor Costs**: Track OpenAI API usage
5. **Scale as Needed**: Adjust batch sizes and intervals

---

## Support and Documentation

- **Architecture**: See `/docs/docker-architecture.md`
- **API Documentation**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/health
- **System Stats**: http://localhost:8000/api/v1/admin/stats

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-22
**Status:** Production Ready
