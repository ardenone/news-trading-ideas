# Docker Setup and Usage

## Overview

The News Trading Ideas MVP uses a multi-stage Docker build to create an optimized production image that includes both the frontend and backend in a single container.

## Architecture

### Multi-Stage Build

1. **Stage 1: Frontend Builder**
   - Base: `node:18-alpine`
   - Builds React frontend
   - Outputs static files to `/app/frontend/dist`

2. **Stage 2: Python Builder**
   - Base: `python:3.11-slim`
   - Installs Python dependencies
   - Optimizes for layer caching

3. **Stage 3: Runtime**
   - Base: `python:3.11-slim`
   - Combines frontend static files and backend
   - Exposes port 8000
   - Runs FastAPI with Uvicorn

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- `.env` file with required environment variables

### Build and Run

```bash
# Build the image
docker build -t news-trading-ideas .

# Run the container
docker run -p 8000:8000 --env-file .env news-trading-ideas

# Or use docker-compose
docker-compose up -d
```

### Access the Application

- **Frontend**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Environment Variables

Required variables in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# News API Configuration
NEWS_API_KEY=your_news_api_key

# Application Configuration
ENVIRONMENT=production
DATABASE_URL=sqlite:///data/news_trading.db
LOG_LEVEL=info

# Optional: Model Configuration
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-large
```

## Docker Compose

### Development Mode

```bash
# Start services
docker-compose up

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Mode with Nginx

```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d

# Access via nginx
curl http://localhost/
```

## Data Persistence

The SQLite database is persisted using Docker volumes:

```yaml
volumes:
  - ./data:/app/data
```

Data location: `/home/jarden/news-trading-ideas/data/news_trading.db`

## Health Checks

The container includes a built-in health check:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' news-trading-ideas

# Manual health check
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T12:00:00Z",
  "version": "1.0.0"
}
```

## Logging

### View Container Logs

```bash
# All logs
docker logs news-trading-ideas

# Follow logs
docker logs -f news-trading-ideas

# Last 100 lines
docker logs --tail 100 news-trading-ideas
```

### Log Levels

Set via `LOG_LEVEL` environment variable:
- `debug`: Detailed debugging information
- `info`: General information (default)
- `warning`: Warning messages
- `error`: Error messages only

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs news-trading-ideas

# Inspect container
docker inspect news-trading-ideas

# Check entrypoint script
docker run --rm news-trading-ideas cat /usr/local/bin/docker-entrypoint.sh
```

### Database Issues

```bash
# Verify database file
docker exec news-trading-ideas ls -lh /app/data/

# Reset database
docker-compose down -v  # Remove volumes
docker-compose up -d     # Recreate
```

### Permission Issues

```bash
# Check file permissions
docker exec news-trading-ideas ls -la /app/data/

# Fix permissions
sudo chown -R $(id -u):$(id -g) ./data
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or use different port
docker run -p 8080:8000 --env-file .env news-trading-ideas
```

## Advanced Usage

### Custom Configuration

```bash
# Override entrypoint
docker run --entrypoint /bin/bash -it news-trading-ideas

# Run with custom command
docker run -p 8000:8000 --env-file .env news-trading-ideas \
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Development Mode

```bash
# Mount source code for hot reload
docker run -p 8000:8000 \
  -v $(pwd)/backend:/app/backend \
  -v $(pwd)/frontend/dist:/app/backend/static \
  --env-file .env \
  news-trading-ideas
```

### Build with Custom Tags

```bash
# Build with version tag
docker build -t news-trading-ideas:v1.0.0 .

# Build with multiple tags
docker build -t news-trading-ideas:latest -t news-trading-ideas:v1.0.0 .
```

## Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` template
2. **Use secrets management** - For production, use Docker secrets or vault
3. **Run as non-root** - Update Dockerfile to use non-root user
4. **Scan for vulnerabilities** - Use `docker scan` or Trivy
5. **Keep base images updated** - Regularly rebuild with latest base images

## Performance Optimization

### Build Cache

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t news-trading-ideas .

# Clear build cache
docker builder prune
```

### Image Size

```bash
# Check image size
docker images news-trading-ideas

# Analyze layers
docker history news-trading-ideas
```

### Resource Limits

```bash
# Limit memory and CPU
docker run -p 8000:8000 \
  --memory="512m" \
  --cpus="1.0" \
  --env-file .env \
  news-trading-ideas
```

## Maintenance

### Cleanup

```bash
# Remove unused images
docker image prune

# Remove unused containers
docker container prune

# Remove unused volumes
docker volume prune

# Complete cleanup
docker system prune -a
```

### Backup

```bash
# Backup database
docker cp news-trading-ideas:/app/data/news_trading.db ./backup/

# Backup with docker-compose
docker-compose exec app tar czf - /app/data > backup.tar.gz
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

## CI/CD Integration

See `.github/workflows/docker-build-test.yml` for automated:
- Building
- Testing
- Security scanning
- Registry pushing

## Support

For issues or questions:
- GitHub Issues: https://github.com/ardenone/news-trading-ideas/issues
- Documentation: `/home/jarden/news-trading-ideas/docs/`
