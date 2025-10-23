# News Trading Ideas Platform - MVP Development Plan

**Version:** 1.0
**Date:** October 22, 2025
**Status:** Ready for Implementation

---

## Executive Summary

This document outlines the complete MVP development plan for a news aggregation and trading ideas platform. The system ingests RSS feeds, groups related headlines using AI, and generates actionable trading ideas with minimal infrastructure and operational costs.

### Key Objectives
- **Cost Efficiency**: Minimize API costs (<$50/month for OpenAI)
- **Simplicity**: Single-server deployment with SQLite
- **Performance**: Process 1000+ articles/day efficiently
- **Scalability**: Architecture allows future growth
- **Time to Market**: 4-6 weeks for MVP

### Success Metrics
- Ingest and process 500+ articles daily
- Group 80%+ related headlines accurately
- Generate 10-20 trading ideas per day
- <2 second response time for UI
- 99% uptime for ingestion pipeline

---

## 1. Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async support, automatic OpenAPI docs)
- **Scheduler**: APScheduler (cron-like task scheduling)
- **RSS Parser**: feedparser (robust RSS/Atom parsing)
- **HTTP Client**: httpx (async HTTP requests)

### Database
- **Primary**: SQLite 3.40+
  - WAL mode for concurrent reads/writes
  - Full-text search (FTS5) for article search
  - JSON support for metadata storage
  - Zero maintenance, single file

### AI/ML
- **Primary LLM**: OpenAI GPT-4o-mini
  - Cost: ~$0.15 per 1M input tokens
  - ~$0.60 per 1M output tokens
  - Fast response times (<1s)
- **Embeddings**: OpenAI text-embedding-3-small
  - Cost: ~$0.02 per 1M tokens
  - 1536 dimensions
- **Vector Search**: sqlite-vec or faiss-lite
  - Native SQLite extension
  - No separate vector DB needed

### Frontend
- **Framework**: React 18+ with Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Charting**: Lightweight Charts or Recharts

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Caddy (automatic HTTPS)
- **Monitoring**: Prometheus + Grafana (optional)
- **Logging**: Structured JSON logs with Python logging

### Development Tools
- **Package Management**: Poetry (Python), pnpm (Node.js)
- **Testing**: pytest, Jest, Playwright
- **Linting**: ruff (Python), ESLint (TypeScript)
- **Type Checking**: mypy (Python), TypeScript
- **Version Control**: Git with conventional commits

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     External Services                        │
├─────────────────────────────────────────────────────────────┤
│  RSS Feeds (Bloomberg, Reuters, WSJ, etc.)                  │
│  OpenAI API (GPT-4o-mini, embeddings)                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │ RSS Ingestion  │  │ AI Processing  │  │   REST API    │ │
│  │   Service      │→ │    Engine      │→ │   (FastAPI)   │ │
│  │  (APScheduler) │  │  (OpenAI)      │  │               │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────┐ │
│  │           SQLite Database (WAL mode)                    │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ Articles | Feeds | Clusters | Ideas | Embeddings | FTS │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
├─────────────────────────────────────────────────────────────┤
│  React SPA → Vite Build → Static Files → Caddy Server      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion Pipeline**
   - Scheduled jobs poll RSS feeds every 5-15 minutes
   - Parse and extract article metadata
   - Deduplicate using URL and content hash
   - Store raw articles in database

2. **AI Processing Pipeline**
   - Generate embeddings for new articles (batched)
   - Cluster related articles using cosine similarity
   - Group clusters into coherent stories
   - Generate trading ideas from high-impact clusters

3. **API Layer**
   - REST endpoints for articles, clusters, ideas
   - WebSocket for real-time updates (optional MVP)
   - Pagination and filtering support
   - Caching layer for frequently accessed data

4. **Frontend**
   - Dashboard with latest news clusters
   - Trading ideas feed with filters
   - Article search and exploration
   - Settings for feed management

---

## 3. Database Schema

### Core Tables

```sql
-- RSS Feed sources
CREATE TABLE feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    category TEXT,
    active BOOLEAN DEFAULT 1,
    last_fetched TIMESTAMP,
    fetch_interval INTEGER DEFAULT 300, -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Articles from RSS feeds
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    content TEXT,
    summary TEXT,
    author TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT, -- for deduplication
    metadata JSON, -- flexible storage for additional data
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);

-- Article embeddings for similarity search
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER UNIQUE NOT NULL,
    embedding BLOB NOT NULL, -- binary format for efficiency
    model TEXT DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

-- Clustered news stories
CREATE TABLE clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    article_count INTEGER DEFAULT 0,
    impact_score REAL, -- 0-100 estimated impact
    confidence REAL, -- 0-1 clustering confidence
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Article-cluster relationship (many-to-many)
CREATE TABLE article_clusters (
    article_id INTEGER NOT NULL,
    cluster_id INTEGER NOT NULL,
    relevance_score REAL, -- 0-1 how relevant to cluster
    PRIMARY KEY (article_id, cluster_id),
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);

-- Trading ideas generated from clusters
CREATE TABLE trading_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT,
    asset_class TEXT, -- stocks, crypto, forex, commodities
    tickers JSON, -- array of relevant tickers
    sentiment TEXT, -- bullish, bearish, neutral
    confidence REAL, -- 0-1
    time_horizon TEXT, -- short, medium, long
    risk_level TEXT, -- low, medium, high
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);

-- Full-text search index
CREATE VIRTUAL TABLE articles_fts USING fts5(
    title,
    content,
    summary,
    content=articles,
    content_rowid=id
);

-- Indexes for performance
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_feed ON articles(feed_id);
CREATE INDEX idx_clusters_created ON clusters(created_at DESC);
CREATE INDEX idx_clusters_impact ON clusters(impact_score DESC);
CREATE INDEX idx_ideas_generated ON trading_ideas(generated_at DESC);
CREATE INDEX idx_ideas_cluster ON trading_ideas(cluster_id);
```

### Database Optimization

- **WAL Mode**: `PRAGMA journal_mode=WAL;` for concurrent access
- **Synchronous Mode**: `PRAGMA synchronous=NORMAL;` for better write performance
- **Cache Size**: `PRAGMA cache_size=-64000;` (64MB cache)
- **Foreign Keys**: `PRAGMA foreign_keys=ON;` for referential integrity

---

## 4. MVP Development Phases

### Phase 1: Core Infrastructure (Week 1-2)

**Objective**: Set up database, RSS ingestion, and basic API

**Tasks**:
1. ✓ Initialize Python project with Poetry
2. ✓ Set up SQLite database with schema
3. ✓ Implement RSS feed manager
   - Add/remove/update feeds
   - Feed validation and health checks
4. ✓ Build ingestion service
   - Scheduled polling (APScheduler)
   - Article parsing and storage
   - Deduplication logic
5. ✓ Create basic FastAPI application
   - CRUD endpoints for feeds
   - CRUD endpoints for articles
   - Health check endpoint
6. ✓ Set up Docker development environment
7. ✓ Write unit tests (>80% coverage)

**Deliverables**:
- Working RSS ingestion pipeline
- SQLite database with sample data
- REST API with OpenAPI documentation
- Docker Compose setup

**Testing Criteria**:
- Ingest 100+ articles from 5 feeds
- Zero duplicate articles
- API response time <100ms
- All tests passing

---

### Phase 2: AI Integration (Week 2-3)

**Objective**: Implement headline grouping and clustering

**Tasks**:
1. ✓ OpenAI API integration
   - Environment-based API key management
   - Rate limiting and retry logic
   - Error handling and fallbacks
2. ✓ Embedding generation service
   - Batch processing for efficiency
   - Store embeddings in database
   - Background job for new articles
3. ✓ Clustering algorithm
   - Cosine similarity calculation
   - DBSCAN or hierarchical clustering
   - Cluster merging and splitting logic
4. ✓ Cluster summarization
   - GPT-4o-mini for summary generation
   - Extract key entities and topics
   - Calculate impact scores
5. ✓ API endpoints for clusters
   - List clusters with pagination
   - Get cluster details with articles
   - Search clusters
6. ✓ Integration tests for AI pipeline

**Deliverables**:
- Automatic article clustering
- Cluster summaries and metadata
- API endpoints for clustered news
- Cost tracking for OpenAI usage

**Testing Criteria**:
- Cluster 500+ articles into 20-50 clusters
- 80%+ clustering accuracy (manual review)
- OpenAI costs <$5 for test dataset
- Cluster generation time <30s for 100 articles

---

### Phase 3: Trading Ideas Generation (Week 3-4)

**Objective**: Generate actionable trading ideas from news clusters

**Tasks**:
1. ✓ Trading idea generation engine
   - Prompt engineering for idea quality
   - Extract tickers and asset classes
   - Sentiment analysis
   - Risk and time horizon estimation
2. ✓ Idea validation and filtering
   - Confidence scoring
   - Remove low-quality ideas
   - Deduplication across clusters
3. ✓ Historical tracking
   - Store all generated ideas
   - Track idea performance (optional)
   - Learn from feedback
4. ✓ API endpoints for trading ideas
   - List ideas with filters
   - Get idea details
   - Search ideas by ticker/asset
5. ✓ Refinement and optimization
   - A/B test different prompts
   - Tune clustering parameters
   - Optimize cost vs quality

**Deliverables**:
- Trading ideas generation pipeline
- API endpoints for ideas
- Admin panel for idea review
- Performance metrics dashboard

**Testing Criteria**:
- Generate 10-20 ideas per day
- 70%+ actionable ideas (manual review)
- Response time <5s per idea
- Clear rationale and supporting data

---

### Phase 4: UI Development (Week 4-6)

**Objective**: Build user-friendly dashboard for news and ideas

**Tasks**:
1. ✓ React project setup with Vite
   - TypeScript configuration
   - Tailwind CSS and shadcn/ui
   - React Query setup
2. ✓ Core UI components
   - Article cards and lists
   - Cluster timeline view
   - Trading ideas feed
   - Filter and search interface
3. ✓ Dashboard pages
   - Home: Latest clusters and ideas
   - News: Browse and search articles
   - Ideas: Trading ideas with filters
   - Settings: Manage feeds and preferences
4. ✓ Real-time updates (optional)
   - WebSocket connection
   - Live article updates
   - Notification system
5. ✓ Responsive design
   - Mobile-friendly layouts
   - Accessibility compliance
   - Dark mode support
6. ✓ Production build and deployment
   - Optimize bundle size
   - Static asset caching
   - Caddy reverse proxy setup

**Deliverables**:
- Fully functional web dashboard
- Mobile-responsive design
- Production-ready deployment
- User documentation

**Testing Criteria**:
- Lighthouse score >90
- Bundle size <500KB gzipped
- Works on mobile and desktop
- E2E tests passing (Playwright)

---

## 5. Integration Architecture

### API Endpoints

**Feeds Management**
```
GET    /api/v1/feeds              - List all feeds
POST   /api/v1/feeds              - Add new feed
GET    /api/v1/feeds/{id}         - Get feed details
PUT    /api/v1/feeds/{id}         - Update feed
DELETE /api/v1/feeds/{id}         - Delete feed
POST   /api/v1/feeds/{id}/refresh - Trigger manual refresh
```

**Articles**
```
GET    /api/v1/articles                  - List articles (paginated)
GET    /api/v1/articles/{id}             - Get article details
GET    /api/v1/articles/search?q=...     - Full-text search
GET    /api/v1/articles/recent?hours=24  - Recent articles
```

**Clusters**
```
GET    /api/v1/clusters                - List clusters (paginated)
GET    /api/v1/clusters/{id}           - Get cluster with articles
GET    /api/v1/clusters/trending       - High-impact clusters
GET    /api/v1/clusters/search?q=...   - Search clusters
```

**Trading Ideas**
```
GET    /api/v1/ideas                    - List ideas (paginated)
GET    /api/v1/ideas/{id}               - Get idea details
GET    /api/v1/ideas/search?ticker=...  - Search by ticker
GET    /api/v1/ideas/filter?asset=...   - Filter by asset class
```

**Admin**
```
GET    /api/v1/admin/stats       - System statistics
GET    /api/v1/admin/costs       - API cost tracking
POST   /api/v1/admin/reprocess   - Reprocess articles
```

### Background Jobs

**High Frequency (Every 5 minutes)**
- Poll high-priority RSS feeds (Bloomberg, Reuters)
- Process new articles through AI pipeline
- Update cluster summaries

**Medium Frequency (Every 15 minutes)**
- Poll standard RSS feeds
- Generate trading ideas from new clusters
- Clean up old cache entries

**Low Frequency (Daily)**
- Database maintenance (VACUUM, ANALYZE)
- Archive old articles (>30 days)
- Generate daily performance reports
- Backup database

### Error Handling Strategy

**RSS Ingestion**
- Retry failed feeds with exponential backoff
- Log feed health issues
- Alert on prolonged failures
- Fallback to cached data

**OpenAI API**
- Retry on rate limits (with backoff)
- Fallback to cached embeddings
- Queue failed requests for retry
- Monitor cost and usage

**Database**
- Transaction rollback on errors
- Automatic backup before migrations
- WAL mode for corruption recovery
- Regular integrity checks

---

## 6. Resource Optimization

### Cost Minimization

**OpenAI API Costs (Estimated Monthly)**

| Operation | Volume | Unit Cost | Monthly Cost |
|-----------|--------|-----------|--------------|
| Embeddings (500 articles/day) | 15K articles | $0.02/1M tokens | ~$5 |
| Clustering summaries (50/day) | 1.5K summaries | $0.15/1M input | ~$10 |
| Trading ideas (20/day) | 600 ideas | $0.60/1M output | ~$15 |
| **Total** | | | **~$30/month** |

**Optimization Strategies**:
- Batch embedding generation (reduce API calls)
- Cache embeddings permanently
- Use GPT-4o-mini instead of GPT-4
- Implement aggressive prompt compression
- Monitor and cap daily spending

**Infrastructure Costs**

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| Server (VPS) | 2 vCPU, 4GB RAM, 80GB SSD | $12-24 |
| Domain + SSL | Cloudflare free tier | $0 |
| Monitoring | Self-hosted Prometheus | $0 |
| **Total** | | **$12-24/month** |

**Total Monthly Operating Cost: $42-54**

### Performance Optimization

**Database**
- Index all foreign keys
- Use covering indexes for common queries
- Implement query result caching (Redis optional)
- Partition old data (archive strategy)

**API**
- Response caching (stale-while-revalidate)
- Database connection pooling
- Async request handling (FastAPI)
- Compression (gzip, brotli)

**Background Jobs**
- Process articles in batches (50-100)
- Parallel embedding generation
- Incremental clustering updates
- Rate limit external API calls

**Frontend**
- Code splitting and lazy loading
- Image optimization (WebP format)
- CDN for static assets (optional)
- Service worker for offline support

### Development Efficiency

**Code Reuse**
- Shared TypeScript types (backend/frontend)
- Component library for UI
- Utility functions package
- Database migration framework (Alembic)

**Testing Strategy**
- Unit tests for core logic (>80% coverage)
- Integration tests for API endpoints
- E2E tests for critical user flows
- Automated testing in CI/CD

**Documentation**
- OpenAPI/Swagger for API
- Inline code documentation
- Architecture decision records (ADRs)
- User guides and tutorials

---

## 7. Risk Assessment & Mitigation

### Technical Risks

**Risk 1: OpenAI API Rate Limits**
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - Implement exponential backoff
  - Queue requests during rate limits
  - Use tier-based rate limiting
  - Monitor usage and adjust batch sizes

**Risk 2: SQLite Performance at Scale**
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - Optimize queries and indexes
  - Archive old data regularly
  - Monitor database size and performance
  - Plan migration path to PostgreSQL

**Risk 3: RSS Feed Quality**
- **Probability**: High
- **Impact**: Medium
- **Mitigation**:
  - Validate feed structure
  - Handle malformed XML gracefully
  - Monitor feed health
  - Maintain backup feed sources

**Risk 4: AI Clustering Accuracy**
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - Manual review and feedback loop
  - A/B test clustering algorithms
  - Tune similarity thresholds
  - Implement confidence scoring

### Business Risks

**Risk 5: API Cost Overruns**
- **Probability**: Low
- **Impact**: High
- **Mitigation**:
  - Set hard spending limits
  - Monitor daily costs
  - Implement cost alerts
  - Cache aggressively

**Risk 6: Data Quality Issues**
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - Implement data validation
  - Manual review process
  - User feedback mechanism
  - Regular data audits

**Risk 7: Competitive Analysis**
- **Probability**: Low
- **Impact**: Low
- **Mitigation**:
  - Focus on unique value proposition
  - Build moat with proprietary data
  - Iterate quickly based on feedback
  - Community building

### Operational Risks

**Risk 8: Server Downtime**
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Automated health checks
  - Database backups (daily)
  - Quick recovery procedures
  - Monitoring and alerting

**Risk 9: Security Vulnerabilities**
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - Regular security updates
  - Input validation and sanitization
  - Rate limiting on API endpoints
  - Security audit before launch

---

## 8. Testing Strategy

### Unit Testing

**Backend (Python)**
- Test all core business logic
- Mock external dependencies (OpenAI, RSS feeds)
- Database operations with in-memory SQLite
- Target: >80% code coverage

**Frontend (TypeScript)**
- Component rendering tests
- Hook and utility function tests
- Mock API responses
- Target: >70% code coverage

### Integration Testing

**API Endpoints**
- Test all CRUD operations
- Validate request/response schemas
- Test authentication and authorization
- Error handling and edge cases

**Background Jobs**
- Test RSS ingestion pipeline
- Test AI processing pipeline
- Test job scheduling and execution
- Verify data consistency

### End-to-End Testing

**Critical User Flows**
- Browse latest news clusters
- Search for specific articles
- View trading ideas
- Filter and sort content

**Tools**: Playwright for browser automation

### Performance Testing

**Load Testing**
- Simulate 100 concurrent users
- Test database query performance
- Measure API response times
- Monitor resource usage

**Tools**: Locust or k6 for load testing

---

## 9. Deployment Guide

### Development Environment

```bash
# 1. Clone repository
git clone <repo-url>
cd news-trading-ideas

# 2. Backend setup
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# 3. Frontend setup (new terminal)
cd frontend
pnpm install
pnpm dev

# 4. Access application
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Production Deployment (Docker)

**1. Environment Configuration**

```bash
# .env file
DATABASE_URL=sqlite:///./data/app.db
OPENAI_API_KEY=sk-...
API_BASE_URL=https://api.example.com
FRONTEND_URL=https://example.com
LOG_LEVEL=INFO
ENABLE_CORS=true
```

**2. Docker Compose Setup**

```yaml
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
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend
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
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

**3. Deploy Commands**

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run database migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart

# Stop services
docker-compose down
```

### Monitoring Setup (Optional)

**Prometheus + Grafana**

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 10. Development Timeline

### Week 1: Foundation
- **Days 1-2**: Project setup, database schema, basic models
- **Days 3-4**: RSS ingestion service, feed management
- **Days 5-7**: FastAPI setup, CRUD endpoints, testing

**Milestone 1**: Working RSS ingestion + REST API

### Week 2: AI Core
- **Days 8-9**: OpenAI integration, embedding generation
- **Days 10-11**: Clustering algorithm implementation
- **Days 12-14**: Cluster summarization, testing, optimization

**Milestone 2**: Automatic article clustering

### Week 3: Trading Ideas
- **Days 15-16**: Trading idea generation engine
- **Days 17-18**: Idea validation and filtering
- **Days 19-21**: API endpoints, refinement, cost optimization

**Milestone 3**: Trading ideas generation

### Week 4: UI Foundation
- **Days 22-23**: React project setup, component library
- **Days 24-25**: Core UI components, layouts
- **Days 26-28**: Dashboard pages, API integration

**Milestone 4**: Basic functional UI

### Week 5: UI Polish
- **Days 29-30**: Search and filter functionality
- **Days 31-32**: Responsive design, mobile optimization
- **Days 33-35**: Real-time updates, notifications

**Milestone 5**: Production-ready UI

### Week 6: Launch Prep
- **Days 36-37**: End-to-end testing, bug fixes
- **Days 38-39**: Performance optimization, security audit
- **Days 40-42**: Deployment, monitoring setup, documentation

**Milestone 6**: MVP Launch

---

## 11. Post-MVP Roadmap

### Phase 5: User Feedback & Iteration (Month 2)
- Collect user feedback
- Improve clustering accuracy
- Refine trading idea quality
- Add user preferences and customization

### Phase 6: Advanced Features (Month 3-4)
- **User Accounts**: Authentication and personalization
- **Email Alerts**: Notify users of high-impact news
- **Historical Analysis**: Track idea performance
- **Advanced Search**: Semantic search using embeddings
- **API Access**: Public API for developers

### Phase 7: Scale & Monetization (Month 5-6)
- **Premium Features**: Advanced analytics, custom feeds
- **Performance Optimization**: Migrate to PostgreSQL
- **Multi-tenant Support**: White-label solution
- **Mobile Apps**: iOS and Android apps
- **Partnerships**: Data providers, brokerages

---

## 12. Success Criteria & KPIs

### Technical KPIs
- **Uptime**: >99% availability
- **Performance**: <2s API response time (p95)
- **Data Quality**: <1% duplicate articles
- **Clustering Accuracy**: >80% relevant groupings
- **Cost Efficiency**: <$60/month operating costs

### Product KPIs
- **Article Volume**: 500+ articles/day processed
- **Clusters**: 20-50 active clusters daily
- **Trading Ideas**: 10-20 actionable ideas daily
- **Idea Quality**: >70% useful ideas (user feedback)

### User KPIs (Post-Launch)
- **Daily Active Users**: 100+ within first month
- **Retention**: >40% 7-day retention
- **Engagement**: >5 minutes avg. session time
- **Satisfaction**: >4.0/5.0 user rating

---

## 13. Appendices

### A. Recommended RSS Feeds

**Financial News**
- Bloomberg: https://www.bloomberg.com/feed/podcast/etf-iq.xml
- Reuters Business: http://feeds.reuters.com/reuters/businessNews
- Wall Street Journal: https://feeds.a.dj.com/rss/RSSMarketsMain.xml
- Financial Times: https://www.ft.com/?format=rss
- CNBC: https://www.cnbc.com/id/100003114/device/rss/rss.html

**Market-Specific**
- CoinDesk (Crypto): https://www.coindesk.com/arc/outboundfeeds/rss/
- Seeking Alpha: https://seekingalpha.com/feed.xml
- MarketWatch: http://feeds.marketwatch.com/marketwatch/topstories/
- Yahoo Finance: https://finance.yahoo.com/rss/

**Economic News**
- Federal Reserve: https://www.federalreserve.gov/feeds/press_all.xml
- ECB: https://www.ecb.europa.eu/rss/press.xml
- IMF: https://www.imf.org/en/News/RSS

### B. Sample Prompts

**Cluster Summarization**
```
You are a financial news analyst. Given these related articles, create a concise summary:

Articles:
{article_titles_and_summaries}

Provide:
1. A 2-sentence summary of the overall story
2. Key entities (companies, people, sectors)
3. Impact score (0-100) based on market significance
4. Confidence (0-1) that these articles are related

Format as JSON.
```

**Trading Idea Generation**
```
Based on this news cluster, generate a trading idea:

Cluster Summary: {summary}
Articles: {article_count}
Key Entities: {entities}

Provide:
1. Title (concise, actionable)
2. Description (2-3 sentences)
3. Rationale (why this is tradeable)
4. Asset class (stocks/crypto/forex/commodities)
5. Relevant tickers (array)
6. Sentiment (bullish/bearish/neutral)
7. Time horizon (short/medium/long)
8. Risk level (low/medium/high)
9. Confidence (0-1)

Format as JSON. Be specific and actionable.
```

### C. Database Backup Strategy

```bash
#!/bin/bash
# Backup script (run daily via cron)

BACKUP_DIR="/app/backups"
DB_PATH="/app/data/app.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
sqlite3 $DB_PATH ".backup ${BACKUP_DIR}/backup_${DATE}.db"

# Compress
gzip ${BACKUP_DIR}/backup_${DATE}.db

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.db.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# rclone copy ${BACKUP_DIR}/backup_${DATE}.db.gz remote:backups/
```

### D. Cost Monitoring Script

```python
# Track OpenAI API costs
import tiktoken
from datetime import datetime, timedelta

def estimate_daily_cost():
    """Calculate estimated daily OpenAI costs"""
    encoding = tiktoken.get_encoding("cl100k_base")

    # Average tokens per article
    avg_article_tokens = 500
    articles_per_day = 500

    # Embeddings cost
    embedding_tokens = articles_per_day * avg_article_tokens
    embedding_cost = (embedding_tokens / 1_000_000) * 0.02

    # Clustering summaries (50 clusters/day, 2000 tokens each)
    cluster_input_tokens = 50 * 2000
    cluster_output_tokens = 50 * 200
    cluster_cost = (cluster_input_tokens / 1_000_000) * 0.15
    cluster_cost += (cluster_output_tokens / 1_000_000) * 0.60

    # Trading ideas (20 ideas/day, 1500 input, 300 output)
    idea_input_tokens = 20 * 1500
    idea_output_tokens = 20 * 300
    idea_cost = (idea_input_tokens / 1_000_000) * 0.15
    idea_cost += (idea_output_tokens / 1_000_000) * 0.60

    total_daily = embedding_cost + cluster_cost + idea_cost
    total_monthly = total_daily * 30

    return {
        "daily": round(total_daily, 2),
        "monthly": round(total_monthly, 2),
        "breakdown": {
            "embeddings": round(embedding_cost, 2),
            "clustering": round(cluster_cost, 2),
            "ideas": round(idea_cost, 2)
        }
    }
```

---

## 14. Conclusion

This MVP development plan provides a comprehensive roadmap for building a news aggregation and trading ideas platform with minimal costs and complexity. The architecture is designed to scale while maintaining simplicity, with clear phases that deliver value incrementally.

### Key Takeaways

1. **Cost-Effective**: <$60/month total operating costs
2. **Simple Stack**: SQLite + FastAPI + React
3. **Fast Development**: 4-6 weeks to MVP
4. **Scalable Design**: Clear upgrade paths for growth
5. **AI-Powered**: Intelligent clustering and idea generation

### Next Steps

1. **Week 1**: Review and approve this plan
2. **Week 2**: Begin Phase 1 development
3. **Weekly**: Progress reviews and adjustments
4. **Week 6**: MVP launch and user feedback
5. **Ongoing**: Iterate based on real-world usage

### Contact & Support

For questions or clarifications on this plan:
- Technical: Review architecture diagrams and code samples
- Timeline: Adjust based on team size and availability
- Scope: Prioritize features based on user needs

---

**Document Version**: 1.0
**Last Updated**: October 22, 2025
**Status**: Ready for Implementation
**Approved By**: [Pending]
