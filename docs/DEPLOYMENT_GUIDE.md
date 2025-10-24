# News Trading Ideas - Deployment Guide

## Overview

This guide covers deployment of the News Trading Ideas MVP Docker container.

## Prerequisites

- Docker installed
- OpenAI API key
- (Optional) Docker Hub account for image hosting
- (Optional) GitHub account for CI/CD

## Local Deployment

### 1. Build the Docker Image

```bash
cd /home/jarden/news-trading-ideas
docker build -t news-trading-ideas:latest .
```

Expected build time: 3-5 minutes

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
OPENAI_API_KEY=sk-your-actual-key-here
RSS_FEEDS=https://feeds.bloomberg.com/markets/news.rss,https://www.cnbc.com/id/100003114/device/rss/rss.html
```

### 3. Run the Container

```bash
docker run -d \
  --name news-trading-ideas \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  news-trading-ideas:latest
```

### 4. Verify Health

```bash
# Wait 30 seconds for startup
sleep 30

# Check health
curl http://localhost:8000/health

# Check logs
docker logs news-trading-ideas
```

Expected output:
```json
{
  "status": "healthy",
  "database": true,
  "openai": true,
  "uptime": 30
}
```

### 5. Access Application

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## Production Deployment

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  news-trading-ideas:
    image: news-trading-ideas:latest
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RSS_FEEDS=${RSS_FEEDS}
      - LOG_LEVEL=info
      - APP_ENV=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Deploy:
```bash
docker-compose up -d
```

### Cloud Deployment Options

#### AWS ECS

```bash
# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag news-trading-ideas:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/news-trading-ideas:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/news-trading-ideas:latest

# Create ECS task definition with environment variables
# Deploy to ECS service
```

#### Google Cloud Run

```bash
# Tag and push to GCR
docker tag news-trading-ideas:latest gcr.io/<project-id>/news-trading-ideas:latest
docker push gcr.io/<project-id>/news-trading-ideas:latest

# Deploy
gcloud run deploy news-trading-ideas \
  --image gcr.io/<project-id>/news-trading-ideas:latest \
  --platform managed \
  --region us-central1 \
  --port 8000 \
  --set-env-vars OPENAI_API_KEY=sk-... \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# Push to ACR
az acr login --name <registry-name>
docker tag news-trading-ideas:latest <registry-name>.azurecr.io/news-trading-ideas:latest
docker push <registry-name>.azurecr.io/news-trading-ideas:latest

# Deploy
az container create \
  --resource-group <group> \
  --name news-trading-ideas \
  --image <registry-name>.azurecr.io/news-trading-ideas:latest \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=sk-... \
  --cpu 2 --memory 4
```

## GitHub CI/CD

### Setup

1. **Add Repository Secrets** (Settings → Secrets):
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password/token

2. **Push to GitHub**:
```bash
git init
git add .
git commit -m "Initial commit: News Trading Ideas MVP"
git branch -M main
git remote add origin git@github.com:ardenone/news-trading-ideas.git
git push -u origin main
```

3. **Automatic Pipeline**:
   - Tests run on every push/PR
   - Docker image built and tested
   - Deployed to Docker Hub on main branch

## Monitoring & Maintenance

### Health Checks

```bash
# Check container health
docker inspect news-trading-ideas --format='{{.State.Health.Status}}'

# View logs
docker logs -f news-trading-ideas

# Check resource usage
docker stats news-trading-ideas
```

### Updating

```bash
# Pull latest code
git pull

# Rebuild image
docker build -t news-trading-ideas:latest .

# Stop and remove old container
docker stop news-trading-ideas
docker rm news-trading-ideas

# Start new container
docker run -d --name news-trading-ideas -p 8000:8000 --env-file .env news-trading-ideas:latest
```

### Backup

```bash
# Backup database
docker cp news-trading-ideas:/app/data/news.db ./backup-$(date +%Y%m%d).db

# Restore database
docker cp ./backup-20251023.db news-trading-ideas:/app/data/news.db
docker restart news-trading-ideas
```

## Scaling Considerations

### PostgreSQL Migration

When ready to scale:

1. **Setup PostgreSQL**:
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=newsdb \
  -e POSTGRES_USER=newsuser \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

2. **Update Environment**:
```env
DATABASE_URL=postgresql://newsuser:password@postgres:5432/newsdb
```

3. **Run Migrations**:
```bash
docker exec news-trading-ideas python -m alembic upgrade head
```

### Load Balancing

For high traffic:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - app1
      - app2

  app1:
    image: news-trading-ideas:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  app2:
    image: news-trading-ideas:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs news-trading-ideas

# Common issues:
# 1. Missing OPENAI_API_KEY
# 2. Port 8000 already in use
# 3. Insufficient memory
```

### Health Check Failing

```bash
# Check individual services
docker exec news-trading-ideas curl http://localhost:8001/health  # Backend
docker exec news-trading-ideas ps aux  # Process list

# Restart container
docker restart news-trading-ideas
```

### Database Locked

```bash
# Stop container
docker stop news-trading-ideas

# Remove database lock
docker run --rm -v $(pwd)/data:/app/data news-trading-ideas:latest rm -f /app/data/news.db-wal /app/data/news.db-shm

# Restart
docker start news-trading-ideas
```

## Security Best Practices

1. **Never commit `.env` file**
2. **Use secrets management** (AWS Secrets Manager, Azure Key Vault, etc.)
3. **Enable HTTPS** (use reverse proxy like Traefik or Caddy)
4. **Limit container resources**:
   ```bash
   docker run -d \
     --memory="1g" \
     --cpus="1.0" \
     ...
   ```
5. **Run as non-root** (already configured in Dockerfile)
6. **Keep dependencies updated**

## Support

For deployment issues:
- Check logs: `docker logs news-trading-ideas`
- GitHub Issues: https://github.com/ardenone/news-trading-ideas/issues
- Documentation: `docs/ARCHITECTURE.md`

---

**Ready for Deployment!** ✅
