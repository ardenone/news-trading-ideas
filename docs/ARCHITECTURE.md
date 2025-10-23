# News Trading Ideas MVP - System Architecture

**Architect:** Docker Architect Agent
**Date:** 2025-10-23
**Version:** 1.0

## Executive Summary

Single Docker container architecture combining FastAPI backend and React frontend, with OpenAI integration for news clustering and trading idea generation. Optimized for simplicity, maintainability, and production deployment.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                          │
│                    (news-trading-ideas)                      │
│                    Exposed Port: 8000                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              NGINX Reverse Proxy                      │  │
│  │  - Route /api/* → FastAPI Backend (uvicorn:8001)     │  │
│  │  - Route /*     → React Frontend (static files)      │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────┐  ┌─────────────────┐  │
│  │      FastAPI Backend             │  │  React Frontend │  │
│  │      (Python 3.11)               │  │  (Build Output) │  │
│  │                                  │  │                 │  │
│  │  Routes:                         │  │  Components:    │  │
│  │  • /health                       │  │  • NewsCluster  │  │
│  │  • /api/news                     │  │  • TradingIdea  │  │
│  │  • /api/clusters                 │  │  • Dashboard    │  │
│  │  • /api/ideas                    │  │  • Settings     │  │
│  └────────┬────────────┬────────────┘  └─────────────────┘  │
│           │            │                                     │
│  ┌────────▼────────┐  ┌▼──────────────────────────────────┐  │
│  │  RSS Ingestion │  │    OpenAI Integration Layer       │  │
│  │  Service       │  │                                   │  │
│  │  (Background)  │  │  • text-embedding-ada-002        │  │
│  │                │  │  • gpt-4-turbo-preview            │  │
│  │  • Scheduler   │  │  • Clustering algorithm           │  │
│  │  • Parser      │  │  • Idea generation                │  │
│  │  • Dedup       │  └───────────────────────────────────┘  │
│  └────────┬────────┘                                        │
│           │                                                 │
│  ┌────────▼──────────────────────────────────────────────┐  │
│  │              SQLite Database                          │  │
│  │                                                       │  │
│  │  Tables:                                              │  │
│  │  • news_articles (id, url, title, content, ...)      │  │
│  │  • news_clusters (id, theme, articles, ...)          │  │
│  │  • trading_ideas (id, cluster_id, idea, ...)         │  │
│  │  • rss_sources (id, url, last_fetch, ...)            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. NGINX Reverse Proxy

**Purpose:** Single entry point for HTTP traffic
**Configuration:** `/etc/nginx/nginx.conf`

```nginx
server {
    listen 8000;

    # Frontend (React SPA)
    location / {
        root /app/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8001/health;
    }
}
```

### 2. FastAPI Backend

**Purpose:** REST API, business logic, OpenAI integration
**Entry Point:** `backend/main.py`
**Port:** 8001 (internal)

#### Directory Structure
```
backend/
├── main.py                 # FastAPI app, routes
├── config.py              # Configuration, env vars
├── models.py              # Pydantic models, DB schemas
├── database.py            # SQLAlchemy setup
├── services/
│   ├── rss_service.py     # RSS ingestion
│   ├── openai_service.py  # OpenAI integration
│   ├── cluster_service.py # Clustering logic
│   └── ideas_service.py   # Trading ideas generation
├── routers/
│   ├── news.py            # News endpoints
│   ├── clusters.py        # Cluster endpoints
│   └── ideas.py           # Ideas endpoints
└── utils/
    ├── scheduler.py       # Background tasks
    └── validators.py      # Input validation
```

#### API Contracts

**News Endpoints:**
```python
GET    /api/news                 # List all news articles
GET    /api/news/{id}            # Get article details
POST   /api/news/refresh         # Trigger RSS refresh
DELETE /api/news/{id}            # Delete article (admin)

Response: NewsArticle {
    id: int
    url: str
    title: str
    content: str
    source: str
    published_at: datetime
    fetched_at: datetime
    cluster_id: Optional[int]
}
```

**Cluster Endpoints:**
```python
GET    /api/clusters             # List all clusters
GET    /api/clusters/{id}        # Get cluster details
POST   /api/clusters/generate    # Generate new clusters

Response: NewsCluster {
    id: int
    theme: str
    summary: str
    article_count: int
    articles: List[NewsArticle]
    confidence_score: float
    created_at: datetime
}
```

**Trading Ideas Endpoints:**
```python
GET    /api/ideas                # List all trading ideas
GET    /api/ideas/{id}           # Get idea details
POST   /api/ideas/generate       # Generate ideas from clusters

Response: TradingIdea {
    id: int
    cluster_id: int
    idea: str
    rationale: str
    confidence: float
    instruments: List[str]
    direction: str  # "long" | "short" | "neutral"
    time_horizon: str
    created_at: datetime
}
```

**Health Endpoint:**
```python
GET    /health

Response: {
    status: "healthy" | "degraded" | "unhealthy"
    database: bool
    openai: bool
    uptime: int
    last_rss_fetch: datetime
}
```

### 3. React Frontend

**Purpose:** User interface, data visualization
**Build Tool:** Vite
**Port:** Static files served by NGINX

#### Directory Structure
```
frontend/
├── src/
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # Entry point
│   ├── components/
│   │   ├── Dashboard.jsx    # Main dashboard
│   │   ├── NewsCluster.jsx  # Cluster display
│   │   ├── TradingIdea.jsx  # Idea card
│   │   ├── NewsList.jsx     # News article list
│   │   ├── Settings.jsx     # Configuration panel
│   │   └── HealthStatus.jsx # System health indicator
│   ├── services/
│   │   └── api.js           # API client
│   ├── hooks/
│   │   └── useNews.js       # Custom hooks
│   └── styles/
│       └── index.css        # Global styles
├── public/
├── index.html
├── vite.config.js
└── package.json
```

#### Component Hierarchy
```
App
├── Dashboard
│   ├── HealthStatus
│   ├── NewsList
│   │   └── NewsArticle (multiple)
│   ├── ClusterList
│   │   └── NewsCluster (multiple)
│   │       └── TradingIdea (0-n)
│   └── Settings
└── ErrorBoundary
```

### 4. OpenAI Integration Layer

**Purpose:** AI-powered clustering and idea generation
**Models Used:**
- `text-embedding-ada-002` - Generate embeddings for clustering
- `gpt-4-turbo-preview` - Generate trading ideas

#### Clustering Algorithm

```python
def cluster_news_articles(articles: List[Article]) -> List[Cluster]:
    """
    1. Generate embeddings for each article using OpenAI
    2. Apply DBSCAN/K-means clustering on embeddings
    3. Extract theme from each cluster using GPT-4
    4. Return clustered articles with themes
    """
    embeddings = [
        openai.embeddings.create(
            model="text-embedding-ada-002",
            input=article.title + " " + article.content
        ) for article in articles
    ]

    clusters = dbscan(embeddings, eps=0.3, min_samples=2)

    for cluster in clusters:
        theme = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "Extract the main theme from these news articles."
            }, {
                "role": "user",
                "content": "\n".join([a.title for a in cluster.articles])
            }]
        )
        cluster.theme = theme.choices[0].message.content

    return clusters
```

#### Trading Ideas Generation

```python
def generate_trading_idea(cluster: Cluster) -> Optional[TradingIdea]:
    """
    1. Analyze cluster theme and articles
    2. Prompt GPT-4 for trading ideas
    3. Parse and validate response
    4. Return structured trading idea or None
    """
    prompt = f"""
    Analyze these related news articles and generate a trading idea:

    Theme: {cluster.theme}
    Articles:
    {format_articles(cluster.articles)}

    Provide:
    - Trading idea (specific, actionable)
    - Rationale (why this makes sense)
    - Instruments (stocks, ETFs, etc.)
    - Direction (long/short/neutral)
    - Time horizon (short/medium/long term)
    - Confidence (0-1)

    If no viable trading idea, respond with "NO_IDEA"
    """

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_trading_idea(response) or None
```

### 5. RSS Ingestion Service

**Purpose:** Fetch, parse, and store news articles
**Schedule:** Configurable (default: every 5 minutes)

#### Workflow

```python
async def fetch_rss_feeds():
    """
    1. Load RSS feed URLs from config/database
    2. Fetch and parse each feed
    3. Extract articles (title, content, URL, date)
    4. Deduplicate against existing articles
    5. Store new articles in database
    6. Log fetch statistics
    """
    for source in rss_sources:
        feed = feedparser.parse(source.url)

        for entry in feed.entries:
            # Check if article already exists (by URL hash)
            if not article_exists(entry.link):
                article = NewsArticle(
                    url=entry.link,
                    title=entry.title,
                    content=extract_content(entry),
                    source=source.name,
                    published_at=parse_date(entry.published)
                )
                db.add(article)

        source.last_fetch = datetime.utcnow()
        db.commit()
```

#### Deduplication Strategy
- URL hash comparison (primary)
- Title similarity (secondary, >90% threshold)
- Content fingerprinting (optional)

### 6. Database Schema

**Type:** SQLite (development), PostgreSQL-ready
**ORM:** SQLAlchemy

```sql
-- News Articles
CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(500) UNIQUE NOT NULL,
    url_hash VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(100) NOT NULL,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cluster_id INTEGER,
    FOREIGN KEY (cluster_id) REFERENCES news_clusters(id)
);

-- News Clusters
CREATE TABLE news_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme VARCHAR(500) NOT NULL,
    summary TEXT,
    article_count INTEGER DEFAULT 0,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Ideas
CREATE TABLE trading_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    idea TEXT NOT NULL,
    rationale TEXT NOT NULL,
    instruments JSON,  -- ["AAPL", "MSFT"]
    direction VARCHAR(20) CHECK(direction IN ('long', 'short', 'neutral')),
    time_horizon VARCHAR(20),
    confidence REAL CHECK(confidence BETWEEN 0 AND 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cluster_id) REFERENCES news_clusters(id)
);

-- RSS Sources
CREATE TABLE rss_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_fetch TIMESTAMP,
    fetch_interval INTEGER DEFAULT 300,  -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_articles_fetched ON news_articles(fetched_at);
CREATE INDEX idx_articles_cluster ON news_articles(cluster_id);
CREATE INDEX idx_clusters_created ON news_clusters(created_at);
CREATE INDEX idx_ideas_cluster ON trading_ideas(cluster_id);
CREATE INDEX idx_ideas_confidence ON trading_ideas(confidence);
```

## Data Flow

### 1. RSS Ingestion Flow
```
Scheduler → RSS Service → Parse Feed → Deduplicate → Database
    ↓
  (every 5 min)
```

### 2. Clustering Flow
```
User Request → API → Fetch Unclustered Articles → OpenAI Embeddings →
Clustering Algorithm → GPT-4 Theme Extraction → Update Database → Response
```

### 3. Trading Ideas Flow
```
User Request → API → Fetch Clusters → For Each Cluster:
    → GPT-4 Analysis → Parse Idea → Validate → Store → Response
```

### 4. Frontend Data Flow
```
User Action → API Call → Backend Processing → JSON Response →
State Update → Component Re-render → UI Update
```

## Security Architecture

### 1. Environment Variables
```env
# Required
OPENAI_API_KEY=sk-***  # Never commit to repo

# Optional with defaults
APP_ENV=production
LOG_LEVEL=info
DATABASE_URL=sqlite:///./news.db
RSS_POLL_INTERVAL=300
CORS_ORIGINS=http://localhost:8000
```

### 2. API Security
- CORS configuration (whitelist origins)
- Rate limiting (prevent abuse)
- Input validation (Pydantic models)
- SQL injection protection (SQLAlchemy ORM)
- XSS protection (React escaping)

### 3. Docker Security
- Non-root user
- Read-only filesystem where possible
- Secret management via environment variables
- Minimal base image (python:3.11-slim)

## Performance Considerations

### 1. Caching Strategy
- Database query results (5 min TTL)
- OpenAI embeddings (permanent, keyed by content hash)
- RSS feed responses (1 min TTL)

### 2. Optimization Techniques
- Batch OpenAI API calls (max 20 articles/request)
- Database connection pooling
- Frontend code splitting
- Static asset caching (1 year)
- NGINX gzip compression

### 3. Resource Limits
```dockerfile
# Docker resource constraints
memory: 1GB
cpu: 1.0
```

## Deployment Architecture

### 1. Docker Build Process
```dockerfile
# Multi-stage build
Stage 1: Frontend Build (Node 18)
  - npm install
  - npm run build
  - Output: /app/frontend/build

Stage 2: Backend Setup (Python 3.11)
  - pip install dependencies
  - Copy backend code
  - Copy frontend build from Stage 1

Stage 3: NGINX Configuration
  - Install nginx
  - Copy nginx.conf
  - Setup supervisor for process management

Final Image: ~300MB
```

### 2. Container Startup
```bash
# Supervisor manages all processes
supervisord.conf:
  - nginx (port 8000)
  - uvicorn (port 8001)
  - rss-scheduler (background)
```

### 3. Health Monitoring
- `/health` endpoint (30s interval)
- Container restart on unhealthy (3 consecutive failures)
- Logging to stdout/stderr (Docker logs)

## Testing Strategy

### 1. Backend Tests (pytest)
- Unit tests (services, models, utils)
- Integration tests (API endpoints, database)
- OpenAI mocking (avoid API costs)
- Coverage target: >80%

### 2. Frontend Tests (Jest + React Testing Library)
- Component rendering
- User interactions
- API integration (mocked)
- Coverage target: >70%

### 3. E2E Tests
- Docker container build
- Container startup
- Health check validation
- Full workflow test (RSS → Cluster → Ideas)

### 4. CI/CD Pipeline
```yaml
GitHub Actions:
  on: [push, pull_request]

  jobs:
    - lint-backend
    - lint-frontend
    - test-backend (pytest)
    - test-frontend (jest)
    - build-docker
    - test-container
    - deploy (main branch only)
```

## Migration Path to PostgreSQL

When ready to scale, migration is straightforward:

```python
# Change DATABASE_URL
sqlite:///./news.db → postgresql://user:pass@host:5432/newsdb

# No code changes needed (SQLAlchemy handles dialect)
# Run Alembic migrations
alembic upgrade head
```

## Monitoring & Observability

### 1. Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation (10MB max, 5 files)

### 2. Metrics
- Request count (by endpoint)
- Response time (p50, p95, p99)
- Error rate
- OpenAI API usage
- RSS fetch success rate

### 3. Alerts
- Container health failures
- OpenAI API errors
- Database connection issues
- High error rates (>5%)

## Success Criteria Validation

| Criterion | Validation Method | Target |
|-----------|------------------|--------|
| Container builds | `docker build` exit code | 0 |
| Container starts | `docker run` + health check | HTTP 200 |
| API functional | Endpoint tests | All pass |
| Frontend loads | Browser automation | Renders correctly |
| RSS ingestion | Background job logs | Articles added |
| Clustering works | OpenAI integration test | Clusters created |
| Ideas generated | GPT-4 response parsing | Valid ideas |
| Tests pass | pytest + jest | >80% coverage |
| CI/CD works | GitHub Actions | Pipeline green |

## Dependencies

### Backend
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
openai==1.3.0
feedparser==6.0.10
python-dotenv==1.0.0
apscheduler==3.10.4
pytest==7.4.3
pytest-cov==4.1.0
httpx==0.25.1
```

### Frontend
```
react==18.2.0
react-dom==18.2.0
vite==5.0.0
axios==1.6.2
@tanstack/react-query==5.8.0
react-router-dom==6.20.0
```

### System
```
nginx==1.24
supervisor==4.2.5
```

## Conclusion

This architecture provides:
- ✅ Single container simplicity
- ✅ Clear separation of concerns
- ✅ Scalable design (PostgreSQL migration path)
- ✅ Production-ready deployment
- ✅ Comprehensive testing
- ✅ Security best practices
- ✅ Observable and maintainable

**Next Steps:**
1. Backend implementation
2. Frontend implementation
3. Docker configuration
4. Testing implementation
5. CI/CD setup

---
**Approval:** Ready for implementation phase
**Architect:** Docker Architect Agent
**Date:** 2025-10-23
