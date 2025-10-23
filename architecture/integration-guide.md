# Technical Integration Guide

**Version:** 1.0
**Date:** October 22, 2025
**Companion to**: MVP Development Plan

---

## 1. Component Integration Map

### System Component Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                    Integration Flow                           │
└──────────────────────────────────────────────────────────────┘

RSS Feeds → Ingestion Service → Article Parser → Database
                ↓                                    ↓
          Deduplication ←─────────────── Content Hash
                ↓
          Embedding Generator (OpenAI) → Embeddings Table
                ↓
          Clustering Engine ←──────── Similarity Search
                ↓
          Cluster Summarizer (GPT-4o-mini) → Clusters Table
                ↓
          Trading Idea Generator → Ideas Table
                ↓
          REST API ←──────────── Frontend (React)
```

### Data Flow Sequence

**1. Article Ingestion**
```python
# Pseudo-code for integration
feed = fetch_rss_feed(feed_url)
for item in feed.entries:
    article = parse_article(item)
    if not is_duplicate(article):
        article_id = save_article(article)
        queue_for_processing(article_id)
```

**2. AI Processing**
```python
# Background job processing
for article_id in processing_queue:
    # Generate embedding
    embedding = openai.create_embedding(article.content)
    save_embedding(article_id, embedding)

    # Find similar articles
    similar = find_similar_articles(embedding, threshold=0.8)

    # Update or create cluster
    cluster = create_or_update_cluster(article_id, similar)

    # Generate summary if new cluster
    if cluster.is_new:
        summary = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": create_summary_prompt(cluster)}]
        )
        cluster.summary = summary.choices[0].message.content
```

**3. Trading Idea Generation**
```python
# Triggered on high-impact clusters
for cluster in get_high_impact_clusters():
    if not cluster.has_trading_idea:
        idea = generate_trading_idea(cluster)
        if idea.confidence > 0.6:
            save_trading_idea(idea)
```

---

## 2. API Integration Patterns

### Backend API Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── dependencies.py      # Shared dependencies
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── article.py
│   │   ├── feed.py
│   │   ├── cluster.py
│   │   └── trading_idea.py
│   │
│   ├── schemas/             # Pydantic schemas
│   │   ├── article.py
│   │   ├── feed.py
│   │   ├── cluster.py
│   │   └── trading_idea.py
│   │
│   ├── api/                 # API routes
│   │   ├── v1/
│   │   │   ├── feeds.py
│   │   │   ├── articles.py
│   │   │   ├── clusters.py
│   │   │   └── ideas.py
│   │   └── deps.py
│   │
│   ├── services/            # Business logic
│   │   ├── rss_ingestion.py
│   │   ├── embedding.py
│   │   ├── clustering.py
│   │   └── idea_generation.py
│   │
│   ├── core/                # Core utilities
│   │   ├── openai_client.py
│   │   ├── cache.py
│   │   └── security.py
│   │
│   └── workers/             # Background jobs
│       ├── scheduler.py
│       ├── feed_poller.py
│       └── ai_processor.py
```

### Sample API Integration Code

**FastAPI Main Application**
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import feeds, articles, clusters, ideas
from app.workers.scheduler import start_scheduler

app = FastAPI(
    title="News Trading Ideas API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feeds.router, prefix="/api/v1/feeds", tags=["feeds"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["clusters"])
app.include_router(ideas.router, prefix="/api/v1/ideas", tags=["ideas"])

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on startup"""
    start_scheduler()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

**Feed Management API**
```python
# app/api/v1/feeds.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.Feed])
def list_feeds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all RSS feeds"""
    feeds = db.query(models.Feed).offset(skip).limit(limit).all()
    return feeds

@router.post("/", response_model=schemas.Feed)
def create_feed(
    feed: schemas.FeedCreate,
    db: Session = Depends(get_db)
):
    """Add a new RSS feed"""
    db_feed = models.Feed(**feed.dict())
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed

@router.post("/{feed_id}/refresh")
async def refresh_feed(feed_id: int, db: Session = Depends(get_db)):
    """Manually trigger feed refresh"""
    from app.services.rss_ingestion import process_feed

    feed = db.query(models.Feed).filter(models.Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    articles_count = await process_feed(feed, db)
    return {"feed_id": feed_id, "articles_processed": articles_count}
```

**Clustering API**
```python
# app/api/v1/clusters.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app import schemas, models
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.Cluster])
def list_clusters(
    skip: int = 0,
    limit: int = 20,
    min_impact: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List news clusters with optional filtering"""
    query = db.query(models.Cluster)

    if min_impact:
        query = query.filter(models.Cluster.impact_score >= min_impact)

    clusters = query.order_by(desc(models.Cluster.created_at)).offset(skip).limit(limit).all()
    return clusters

@router.get("/{cluster_id}", response_model=schemas.ClusterDetail)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)):
    """Get cluster details with articles"""
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.get("/trending", response_model=List[schemas.Cluster])
def get_trending_clusters(
    limit: int = 10,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get trending clusters by impact score"""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    clusters = (
        db.query(models.Cluster)
        .filter(models.Cluster.created_at >= cutoff)
        .order_by(desc(models.Cluster.impact_score))
        .limit(limit)
        .all()
    )
    return clusters
```

---

## 3. Frontend Integration

### React Application Structure

```
frontend/
├── src/
│   ├── main.tsx             # Application entry
│   ├── App.tsx              # Root component
│   ├── vite-env.d.ts        # TypeScript definitions
│   │
│   ├── api/                 # API client
│   │   ├── client.ts        # Axios instance
│   │   ├── feeds.ts
│   │   ├── articles.ts
│   │   ├── clusters.ts
│   │   └── ideas.ts
│   │
│   ├── components/          # Reusable components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── ArticleCard.tsx
│   │   ├── ClusterTimeline.tsx
│   │   ├── IdeaCard.tsx
│   │   └── SearchBar.tsx
│   │
│   ├── pages/               # Page components
│   │   ├── Home.tsx
│   │   ├── News.tsx
│   │   ├── Ideas.tsx
│   │   └── Settings.tsx
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── useArticles.ts
│   │   ├── useClusters.ts
│   │   └── useIdeas.ts
│   │
│   ├── types/               # TypeScript types
│   │   ├── article.ts
│   │   ├── cluster.ts
│   │   └── idea.ts
│   │
│   └── lib/                 # Utilities
│       ├── utils.ts
│       └── constants.ts
```

### API Client Setup

**Base API Client**
```typescript
// src/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Clusters API Client**
```typescript
// src/api/clusters.ts
import { apiClient } from './client';
import type { Cluster, ClusterDetail } from '@/types/cluster';

export const clustersApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    min_impact?: number;
  }): Promise<Cluster[]> => {
    const { data } = await apiClient.get('/clusters', { params });
    return data;
  },

  get: async (id: number): Promise<ClusterDetail> => {
    const { data } = await apiClient.get(`/clusters/${id}`);
    return data;
  },

  trending: async (params?: {
    limit?: number;
    hours?: number;
  }): Promise<Cluster[]> => {
    const { data } = await apiClient.get('/clusters/trending', { params });
    return data;
  },
};
```

### React Query Integration

**Custom Hooks**
```typescript
// src/hooks/useClusters.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { clustersApi } from '@/api/clusters';

export function useClusters(params?: {
  skip?: number;
  limit?: number;
  min_impact?: number;
}) {
  return useQuery({
    queryKey: ['clusters', params],
    queryFn: () => clustersApi.list(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useCluster(id: number) {
  return useQuery({
    queryKey: ['cluster', id],
    queryFn: () => clustersApi.get(id),
    enabled: !!id,
  });
}

export function useTrendingClusters(hours: number = 24) {
  return useQuery({
    queryKey: ['clusters', 'trending', hours],
    queryFn: () => clustersApi.trending({ hours, limit: 10 }),
    refetchInterval: 60000, // Refresh every minute
  });
}
```

**Component Usage**
```typescript
// src/pages/Home.tsx
import { useTrendingClusters } from '@/hooks/useClusters';
import { ClusterCard } from '@/components/ClusterCard';
import { Skeleton } from '@/components/ui/skeleton';

export function Home() {
  const { data: clusters, isLoading, error } = useTrendingClusters(24);

  if (isLoading) {
    return (
      <div className="grid gap-4">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return <div>Error loading clusters: {error.message}</div>;
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Trending News</h1>
      <div className="grid gap-4">
        {clusters?.map((cluster) => (
          <ClusterCard key={cluster.id} cluster={cluster} />
        ))}
      </div>
    </div>
  );
}
```

---

## 4. Background Job Integration

### APScheduler Setup

```python
# app/workers/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.workers.feed_poller import poll_all_feeds
from app.workers.ai_processor import process_pending_articles
from app.database import SessionLocal

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Initialize and start background job scheduler"""

    # Poll high-priority feeds every 5 minutes
    scheduler.add_job(
        poll_all_feeds,
        trigger=IntervalTrigger(minutes=5),
        id="poll_high_priority_feeds",
        kwargs={"priority": "high"},
        replace_existing=True,
    )

    # Poll standard feeds every 15 minutes
    scheduler.add_job(
        poll_all_feeds,
        trigger=IntervalTrigger(minutes=15),
        id="poll_standard_feeds",
        kwargs={"priority": "standard"},
        replace_existing=True,
    )

    # Process articles with AI every 10 minutes
    scheduler.add_job(
        process_pending_articles,
        trigger=IntervalTrigger(minutes=10),
        id="process_ai_pipeline",
        replace_existing=True,
    )

    # Daily maintenance at 3 AM
    scheduler.add_job(
        database_maintenance,
        trigger=CronTrigger(hour=3, minute=0),
        id="database_maintenance",
        replace_existing=True,
    )

    scheduler.start()

async def database_maintenance():
    """Daily database cleanup and optimization"""
    db = SessionLocal()
    try:
        # Archive old articles
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Vacuum database
        db.execute("VACUUM")
        db.execute("ANALYZE")

        db.commit()
    finally:
        db.close()
```

### RSS Polling Worker

```python
# app/workers/feed_poller.py
import feedparser
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Feed, Article
from app.database import SessionLocal

async def poll_all_feeds(priority: str = "standard"):
    """Poll all active feeds and store new articles"""
    db = SessionLocal()
    try:
        feeds = db.query(Feed).filter(
            Feed.active == True,
            Feed.priority == priority
        ).all()

        for feed in feeds:
            try:
                await process_feed(feed, db)
            except Exception as e:
                print(f"Error processing feed {feed.name}: {e}")

        db.commit()
    finally:
        db.close()

async def process_feed(feed: Feed, db: Session) -> int:
    """Process a single RSS feed"""
    parsed = feedparser.parse(feed.url)
    articles_added = 0

    for entry in parsed.entries:
        # Create content hash for deduplication
        content = f"{entry.title}{entry.link}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if article already exists
        existing = db.query(Article).filter(
            Article.content_hash == content_hash
        ).first()

        if not existing:
            article = Article(
                feed_id=feed.id,
                title=entry.title,
                url=entry.link,
                content=entry.get('description', ''),
                summary=entry.get('summary', ''),
                author=entry.get('author'),
                published_at=parse_date(entry.get('published')),
                content_hash=content_hash,
                metadata={
                    "tags": entry.get('tags', []),
                    "category": entry.get('category'),
                }
            )
            db.add(article)
            articles_added += 1

    # Update feed last_fetched timestamp
    feed.last_fetched = datetime.utcnow()
    db.commit()

    return articles_added

def parse_date(date_string: str) -> datetime:
    """Parse various date formats from RSS feeds"""
    from dateutil import parser
    try:
        return parser.parse(date_string)
    except:
        return datetime.utcnow()
```

### AI Processing Worker

```python
# app/workers/ai_processor.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Article, Embedding, Cluster
from app.services.embedding import generate_embeddings
from app.services.clustering import cluster_articles
from app.database import SessionLocal

async def process_pending_articles():
    """Process articles without embeddings"""
    db = SessionLocal()
    try:
        # Get articles without embeddings
        articles = db.query(Article).outerjoin(Embedding).filter(
            Embedding.id == None
        ).limit(100).all()

        if not articles:
            return

        # Generate embeddings in batch
        await generate_embeddings(articles, db)

        # Run clustering
        await cluster_articles(db)

        db.commit()
    finally:
        db.close()
```

---

## 5. OpenAI Integration

### OpenAI Client Wrapper

```python
# app/core/openai_client.py
from openai import AsyncOpenAI
from typing import List
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def create_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Generate embedding for text"""
    response = await client.embeddings.create(
        model=model,
        input=text,
    )
    return response.data[0].embedding

async def create_embeddings_batch(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """Generate embeddings for multiple texts"""
    response = await client.embeddings.create(
        model=model,
        input=texts,
    )
    return [item.embedding for item in response.data]

async def generate_completion(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> str:
    """Generate text completion"""
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
```

### Embedding Service

```python
# app/services/embedding.py
import numpy as np
from typing import List
from sqlalchemy.orm import Session
from app.models import Article, Embedding
from app.core.openai_client import create_embeddings_batch

async def generate_embeddings(articles: List[Article], db: Session):
    """Generate embeddings for articles"""
    # Prepare texts
    texts = [
        f"{article.title}\n\n{article.summary or article.content[:500]}"
        for article in articles
    ]

    # Generate embeddings in batch
    embeddings = await create_embeddings_batch(texts)

    # Store embeddings
    for article, embedding_vector in zip(articles, embeddings):
        # Convert to bytes for storage
        embedding_bytes = np.array(embedding_vector, dtype=np.float32).tobytes()

        embedding = Embedding(
            article_id=article.id,
            embedding=embedding_bytes,
            model="text-embedding-3-small"
        )
        db.add(embedding)

    db.commit()

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### Clustering Service

```python
# app/services/clustering.py
import numpy as np
from typing import List, Set
from sqlalchemy.orm import Session
from sklearn.cluster import DBSCAN
from app.models import Article, Embedding, Cluster, ArticleCluster
from app.core.openai_client import generate_completion

async def cluster_articles(db: Session, min_samples: int = 2, eps: float = 0.3):
    """Cluster articles based on embeddings"""
    # Get articles with embeddings but not in clusters
    articles = db.query(Article).join(Embedding).outerjoin(ArticleCluster).filter(
        ArticleCluster.article_id == None
    ).all()

    if len(articles) < min_samples:
        return

    # Load embeddings
    embeddings = []
    article_ids = []
    for article in articles:
        embedding_bytes = db.query(Embedding.embedding).filter(
            Embedding.article_id == article.id
        ).scalar()
        embedding_vector = np.frombuffer(embedding_bytes, dtype=np.float32)
        embeddings.append(embedding_vector)
        article_ids.append(article.id)

    # Run DBSCAN clustering
    embeddings_matrix = np.array(embeddings)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embeddings_matrix)

    # Create clusters
    unique_labels = set(labels)
    for label in unique_labels:
        if label == -1:  # Noise points
            continue

        # Get articles in this cluster
        cluster_article_ids = [
            article_ids[i] for i, l in enumerate(labels) if l == label
        ]
        cluster_articles = db.query(Article).filter(
            Article.id.in_(cluster_article_ids)
        ).all()

        # Generate cluster summary
        summary = await generate_cluster_summary(cluster_articles)

        # Create cluster
        cluster = Cluster(
            title=summary['title'],
            summary=summary['summary'],
            article_count=len(cluster_articles),
            impact_score=summary['impact_score'],
            confidence=summary['confidence'],
        )
        db.add(cluster)
        db.flush()

        # Link articles to cluster
        for article_id in cluster_article_ids:
            article_cluster = ArticleCluster(
                article_id=article_id,
                cluster_id=cluster.id,
                relevance_score=1.0,
            )
            db.add(article_cluster)

    db.commit()

async def generate_cluster_summary(articles: List[Article]) -> dict:
    """Generate summary for a cluster of articles"""
    # Prepare article data
    article_data = "\n\n".join([
        f"Title: {article.title}\nSummary: {article.summary or article.content[:200]}"
        for article in articles[:10]  # Limit to 10 articles
    ])

    prompt = f"""Analyze these related news articles and provide:
1. A concise title (max 10 words)
2. A 2-sentence summary
3. Impact score (0-100) based on market significance
4. Confidence (0-1) that these articles are related

Articles:
{article_data}

Respond in JSON format:
{{
    "title": "...",
    "summary": "...",
    "impact_score": 75,
    "confidence": 0.9
}}
"""

    response = await generate_completion(prompt, max_tokens=300)

    # Parse JSON response
    import json
    return json.loads(response)
```

---

## 6. Docker Integration

### Multi-Stage Dockerfile (Backend)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Run database migrations on startup
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Multi-Stage Dockerfile (Frontend)

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Build application
COPY . .
RUN pnpm build

FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000/api/v1
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

### Caddyfile Configuration

```
# Caddyfile
{
    email admin@example.com
}

example.com {
    # Frontend
    reverse_proxy /* frontend:80

    # API
    reverse_proxy /api/* backend:8000

    # Enable compression
    encode gzip

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000;"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer-when-downgrade"
    }
}
```

---

## 7. Testing Integration

### Backend Test Setup

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    """Create test client"""
    def override_get_db():
        yield db_session

    from app.dependencies import get_db
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

```python
# backend/tests/test_feeds.py
def test_create_feed(client):
    """Test creating a new feed"""
    response = client.post(
        "/api/v1/feeds/",
        json={
            "name": "Test Feed",
            "url": "https://example.com/rss",
            "category": "tech"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Feed"
    assert data["url"] == "https://example.com/rss"

def test_list_feeds(client, db_session):
    """Test listing feeds"""
    # Create test feeds
    from app.models import Feed
    db_session.add(Feed(name="Feed 1", url="https://example.com/1"))
    db_session.add(Feed(name="Feed 2", url="https://example.com/2"))
    db_session.commit()

    response = client.get("/api/v1/feeds/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
```

### Frontend Test Setup

```typescript
// frontend/src/test/setup.ts
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

afterEach(() => {
  cleanup();
});
```

```typescript
// frontend/src/components/__tests__/ClusterCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ClusterCard } from '../ClusterCard';

describe('ClusterCard', () => {
  it('renders cluster title', () => {
    const cluster = {
      id: 1,
      title: 'Test Cluster',
      summary: 'Test summary',
      article_count: 5,
      impact_score: 75,
    };

    render(<ClusterCard cluster={cluster} />);
    expect(screen.getByText('Test Cluster')).toBeInTheDocument();
  });
});
```

---

## 8. Monitoring Integration

### Logging Setup

```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/app/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
for handler in logger.handlers:
    handler.setFormatter(JSONFormatter())
```

### Prometheus Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
articles_processed = Counter(
    'articles_processed_total',
    'Total articles processed'
)

clusters_created = Counter(
    'clusters_created_total',
    'Total clusters created'
)

ideas_generated = Counter(
    'ideas_generated_total',
    'Total trading ideas generated'
)

openai_api_calls = Counter(
    'openai_api_calls_total',
    'Total OpenAI API calls',
    ['operation']
)

active_feeds = Gauge(
    'active_feeds',
    'Number of active RSS feeds'
)
```

---

## Summary

This integration guide provides detailed technical specifications for connecting all system components. Key integration points:

1. **API Layer**: FastAPI with clear endpoint structure
2. **Data Layer**: SQLite with optimized schema
3. **AI Layer**: OpenAI integration with batching
4. **Frontend**: React with TypeScript and React Query
5. **Background Jobs**: APScheduler for automated tasks
6. **Deployment**: Docker Compose with Caddy
7. **Testing**: Comprehensive test coverage
8. **Monitoring**: Logging and metrics

All components are designed to work together seamlessly with clear interfaces and error handling.
