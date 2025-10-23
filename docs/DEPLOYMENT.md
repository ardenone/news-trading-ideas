# Deployment Guide

## Overview

This guide covers deployment options for the News Trading Ideas MVP platform.

## Deployment Options

### 1. Docker Single Container (Recommended for MVP)

#### Prerequisites
- Docker 20.10+
- Server with 2GB RAM minimum
- Open port 8000 or 80

#### Steps

```bash
# 1. Clone repository
git clone https://github.com/ardenone/news-trading-ideas.git
cd news-trading-ideas

# 2. Configure environment
cp .env.example .env
nano .env  # Add API keys

# 3. Build image
docker build -t news-trading-ideas .

# 4. Run container
docker run -d \
  --name news-trading-ideas \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  news-trading-ideas

# 5. Verify deployment
curl http://localhost:8000/health
```

### 2. Docker Compose (Development/Staging)

```bash
# 1. Start services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

### 3. Cloud Deployment

#### AWS EC2

```bash
# 1. Launch EC2 instance (t3.small or larger)
# 2. Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 3. Deploy application
git clone https://github.com/ardenone/news-trading-ideas.git
cd news-trading-ideas
docker-compose up -d

# 4. Configure security group
# - Allow inbound TCP 8000 or 80
```

#### Google Cloud Run

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/[PROJECT-ID]/news-trading-ideas

# 2. Deploy to Cloud Run
gcloud run deploy news-trading-ideas \
  --image gcr.io/[PROJECT-ID]/news-trading-ideas \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your_key,NEWS_API_KEY=your_key
```

#### Azure Container Instances

```bash
# 1. Create resource group
az group create --name news-trading-rg --location eastus

# 2. Create container registry
az acr create --resource-group news-trading-rg \
  --name newstradingacr --sku Basic

# 3. Build and push
az acr build --registry newstradingacr \
  --image news-trading-ideas:latest .

# 4. Deploy container
az container create \
  --resource-group news-trading-rg \
  --name news-trading-ideas \
  --image newstradingacr.azurecr.io/news-trading-ideas:latest \
  --dns-name-label news-trading-mvp \
  --ports 8000
```

#### DigitalOcean App Platform

```bash
# 1. Create app.yaml
cat > .do/app.yaml << EOF
name: news-trading-ideas
services:
- name: web
  dockerfile_path: Dockerfile
  github:
    repo: ardenone/news-trading-ideas
    branch: main
  http_port: 8000
  envs:
  - key: OPENAI_API_KEY
    scope: RUN_TIME
    type: SECRET
  - key: NEWS_API_KEY
    scope: RUN_TIME
    type: SECRET
EOF

# 2. Deploy via CLI or dashboard
doctl apps create --spec .do/app.yaml
```

### 4. Kubernetes (Production Scale)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: news-trading-ideas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: news-trading-ideas
  template:
    metadata:
      labels:
        app: news-trading-ideas
    spec:
      containers:
      - name: news-trading-ideas
        image: ghcr.io/ardenone/news-trading-ideas:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: news-trading-secrets
              key: openai-api-key
        - name: NEWS_API_KEY
          valueFrom:
            secretKeyRef:
              name: news-trading-secrets
              key: news-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: news-trading-service
spec:
  selector:
    app: news-trading-ideas
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Configuration

### Environment Variables

Production `.env`:

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...

# Application
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=sqlite:///data/news_trading.db

# Security (add in production)
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Performance
WORKERS=4
MAX_CONNECTIONS=100
```

### Database

For production, consider PostgreSQL:

```bash
# Update .env
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Update requirements.txt
echo "psycopg2-binary==2.9.9" >> backend/requirements.txt
```

### SSL/TLS

#### Using Nginx Reverse Proxy

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Using Caddy (Automatic SSL)

```caddyfile
your-domain.com {
    reverse_proxy localhost:8000
}
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl https://your-domain.com/health

# Detailed status
curl https://your-domain.com/api/status
```

### Logging

```bash
# Docker logs
docker logs -f news-trading-ideas

# Export logs
docker logs news-trading-ideas > app.log

# With timestamp
docker logs -t news-trading-ideas
```

### Metrics

Set up Prometheus and Grafana:

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Backup and Recovery

### Database Backup

```bash
# Manual backup
docker exec news-trading-ideas sqlite3 /app/data/news_trading.db ".backup /app/data/backup.db"
docker cp news-trading-ideas:/app/data/backup.db ./backups/

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec news-trading-ideas sqlite3 /app/data/news_trading.db ".backup /app/data/backup_${DATE}.db"
docker cp news-trading-ideas:/app/data/backup_${DATE}.db ./backups/
find ./backups -mtime +7 -delete  # Keep 7 days
EOF

chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Restore

```bash
# Stop container
docker stop news-trading-ideas

# Restore database
docker cp ./backups/backup.db news-trading-ideas:/app/data/news_trading.db

# Start container
docker start news-trading-ideas
```

## Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Using docker-compose
docker-compose up -d --scale app=3

# Using Kubernetes
kubectl scale deployment news-trading-ideas --replicas=5
```

### Vertical Scaling (Resource Limits)

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
          cpus: '1.0'
          memory: 1G
```

## Security Checklist

- [ ] API keys stored in secrets, not in code
- [ ] HTTPS enabled with valid certificate
- [ ] Firewall configured (only required ports open)
- [ ] Regular security updates applied
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Container running as non-root user
- [ ] Security headers configured

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs news-trading-ideas

# Verify environment
docker exec news-trading-ideas env

# Test entrypoint
docker run --rm --entrypoint /bin/bash news-trading-ideas -c "env"
```

### High Memory Usage

```bash
# Check stats
docker stats news-trading-ideas

# Limit resources
docker update --memory="512m" news-trading-ideas
```

### Slow Response Times

```bash
# Check container resources
docker stats

# Check application logs
docker logs news-trading-ideas | grep -i "slow\|timeout"

# Profile application
docker exec news-trading-ideas pip install py-spy
docker exec news-trading-ideas py-spy top --pid 1
```

## Rollback

```bash
# Using Docker tags
docker pull ghcr.io/ardenone/news-trading-ideas:v1.0.0
docker stop news-trading-ideas
docker rm news-trading-ideas
docker run -d --name news-trading-ideas \
  -p 8000:8000 --env-file .env \
  ghcr.io/ardenone/news-trading-ideas:v1.0.0
```

## CI/CD Pipeline

The GitHub Actions workflow automatically:
1. Builds Docker image on push to main
2. Runs tests
3. Scans for security vulnerabilities
4. Pushes to GitHub Container Registry
5. Deploys to production (if configured)

See `.github/workflows/docker-build-test.yml` for details.

## Support

For deployment issues:
- GitHub Issues: https://github.com/ardenone/news-trading-ideas/issues
- Documentation: `/home/jarden/news-trading-ideas/docs/`
