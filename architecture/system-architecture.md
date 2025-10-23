# News Trading Ideas System - System Architecture

**Version:** 1.0.0
**Date:** 2025-10-22
**Status:** MVP Design
**Architect:** System Architecture Designer

---

## Executive Summary

This document outlines the architecture for an MVP news trading ideas system that ingests financial news via RSS feeds, groups articles by events using LLM clustering, ranks events by relevance, and generates trading ideas for the top events. The architecture prioritizes minimal resource usage, simple deployment, and rapid iteration while maintaining clean separation of concerns for future scalability.

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WEB INTERFACE LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │  Dashboard   │  │  Events      │  │  Trading Ideas          │  │
│  │  View        │  │  Explorer    │  │  View                   │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────┴────────────────────────────────────────┐
│                       API SERVICE LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application Server                                   │  │
│  │  • REST API Endpoints                                         │  │
│  │  • WebSocket for real-time updates                            │  │
│  │  • Static file serving                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │   Feed      │  │   Event      │  │   Trading Idea         │    │
│  │   Ingestion │→ │   Clustering │→ │   Generator            │    │
│  │   Service   │  │   Service    │  │   Service              │    │
│  └─────────────┘  └──────────────┘  └────────────────────────┘    │
│         ↓                  ↓                      ↓                  │
└─────────┼──────────────────┼──────────────────────┼─────────────────┘
          │                  │                      │
┌─────────┴──────────────────┴──────────────────────┴─────────────────┐
│                       DATA LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  SQLite Database                                              │  │
│  │  • articles table                                             │  │
│  │  • events table                                               │  │
│  │  • trading_ideas table                                        │  │
│  │  • feed_metadata table                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐     │
│  │  Task       │  │  OpenAI API  │  │  Logging &             │     │
│  │  Scheduler  │  │  Client      │  │  Monitoring            │     │
│  │  (APScheduler)  (GPT-4/mini) │  │  (structlog)           │     │
│  └─────────────┘  └──────────────┘  └────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Browser)                           │
│  • React/Vue.js (or vanilla JS for MVP)                             │
│  • Chart.js for visualizations                                       │
│  • WebSocket client for real-time updates                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Endpoints:                                                          │
│  • GET  /api/feeds              - List configured feeds              │
│  • POST /api/feeds/refresh      - Manual refresh trigger            │
│  • GET  /api/events             - Get grouped events                │
│  • GET  /api/events/{id}        - Get event details                 │
│  • GET  /api/trading-ideas      - Get trading ideas                 │
│  • GET  /api/dashboard          - Dashboard summary                 │
│  • WS   /ws/updates             - Real-time notifications           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┬─────────────┐
                ▼                         ▼             ▼
┌───────────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  FEED INGESTION       │  │  EVENT CLUSTERING│  │  IDEA GENERATOR │
│  SERVICE              │  │  SERVICE         │  │  SERVICE        │
├───────────────────────┤  ├──────────────────┤  ├─────────────────┤
│ • RSS Parser          │  │ • LLM Clustering │  │ • GPT-4 API     │
│ • Article Extractor   │  │ • Event Ranking  │  │ • Prompt Mgmt   │
│ • Deduplication       │  │ • Source Count   │  │ • Idea Storage  │
│ • Queue Manager       │  │ • Timestamp Rank │  │ • Top-10 Filter │
│ • Adaptive Scheduler  │  │ • Event Merging  │  │                 │
└───────┬───────────────┘  └────────┬─────────┘  └────────┬────────┘
        │                           │                      │
        └───────────────┬───────────┴──────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  • Repository Pattern                                                │
│  • SQLAlchemy ORM                                                    │
│  • Connection Pooling                                                │
│  • Transaction Management                                            │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SQLite DATABASE                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Tables:                                                             │
│  • articles (id, url, title, content, published_at, source, ...)    │
│  • events (id, name, description, article_count, latest_at, ...)    │
│  • event_articles (event_id, article_id) - many-to-many             │
│  • trading_ideas (id, event_id, idea, reasoning, created_at, ...)   │
│  • feed_metadata (feed_url, last_fetch, article_count, ...)         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Architecture

### 3.1 Feed Ingestion Flow

```
┌──────────┐
│ Scheduler│
│ (APSched)│
└────┬─────┘
     │ Triggers refresh based on adaptive timing
     ▼
┌────────────────────────────────────────────────────┐
│ FEED INGESTION SERVICE                             │
│                                                    │
│ 1. Fetch RSS feeds (async HTTP requests)          │
│    └─> feedparser library                         │
│                                                    │
│ 2. Parse articles from feeds                      │
│    └─> Extract: title, link, published, source    │
│                                                    │
│ 3. Deduplication check                            │
│    └─> Query DB for existing URLs                 │
│                                                    │
│ 4. Store new articles                             │
│    └─> Batch insert to articles table             │
│                                                    │
│ 5. Update feed metadata                           │
│    └─> last_fetch_time, article_count             │
│                                                    │
│ 6. Calculate next refresh time                    │
│    └─> min(time_for_5_articles, 15_min)           │
│                                                    │
│ 7. Trigger event clustering (if new articles)     │
│    └─> Async task queue                           │
└────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│ SQLite Database │
│ • articles      │
│ • feed_metadata │
└─────────────────┘
```

### 3.2 Event Clustering Flow

```
┌─────────────────────────────┐
│ New articles detected       │
└──────────┬──────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│ EVENT CLUSTERING SERVICE                             │
│                                                      │
│ 1. Fetch unclustered articles                       │
│    └─> SELECT * FROM articles WHERE event_id IS NULL│
│                                                      │
│ 2. Batch articles (up to 50 at a time)              │
│    └─> To stay within GPT-4-mini token limits       │
│                                                      │
│ 3. Call GPT-4-mini for clustering                   │
│    └─> Prompt: "Group these headlines by event"     │
│    └─> Response: JSON with event groups             │
│                                                      │
│ 4. Create/update events                             │
│    └─> Merge with existing events by similarity     │
│    └─> Update article_count, latest_timestamp       │
│                                                      │
│ 5. Link articles to events                          │
│    └─> INSERT INTO event_articles                   │
│                                                      │
│ 6. Rank events                                      │
│    └─> Score = source_count * 10 + recency_score    │
│    └─> UPDATE events SET rank_score                 │
│                                                      │
│ 7. Trigger trading idea generation (top 10)         │
│    └─> Async task for top-ranked events             │
└──────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│ SQLite Database │
│ • events        │
│ • event_articles│
└─────────────────┘
```

### 3.3 Trading Idea Generation Flow

```
┌─────────────────────────────┐
│ Top 10 events identified    │
└──────────┬──────────────────┘
           ▼
┌──────────────────────────────────────────────────────┐
│ TRADING IDEA GENERATOR SERVICE                       │
│                                                      │
│ 1. Fetch top 10 events (by rank_score)              │
│    └─> SELECT * FROM events ORDER BY rank_score     │
│                                                      │
│ 2. For each event:                                   │
│    a. Gather event context                          │
│       └─> Event name, description, article titles   │
│                                                      │
│    b. Build GPT-4 prompt                            │
│       └─> Context + "Generate trading ideas"        │
│                                                      │
│    c. Call GPT-4 API (parallel requests)            │
│       └─> Use structured output for consistency     │
│                                                      │
│    d. Parse trading idea response                   │
│       └─> Extract: idea, reasoning, instruments     │
│                                                      │
│    e. Store trading idea                            │
│       └─> INSERT INTO trading_ideas                 │
│                                                      │
│ 3. Mark events as processed                         │
│    └─> UPDATE events SET has_trading_idea = true    │
│                                                      │
│ 4. Notify frontend via WebSocket                    │
│    └─> Send update notification                     │
└──────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐
│ SQLite Database │
│ • trading_ideas │
└─────────────────┘
```

---

## 4. Module Breakdown

### 4.1 Core Services

#### **Feed Ingestion Service**
```
src/services/feed_ingestion.py

Responsibilities:
• Fetch RSS feeds asynchronously
• Parse and normalize article data
• Deduplicate articles by URL
• Store new articles in database
• Calculate adaptive refresh intervals
• Schedule next feed refresh

Dependencies:
• httpx (async HTTP client)
• feedparser (RSS parsing)
• APScheduler (task scheduling)
• SQLAlchemy (database access)

Configuration:
• Feed URLs list
• Refresh interval bounds (min: 5 articles worth, max: 15 min)
• HTTP timeout settings
• Concurrent fetch limit
```

#### **Event Clustering Service**
```
src/services/event_clustering.py

Responsibilities:
• Fetch unclustered articles from database
• Batch articles for efficient LLM processing
• Call GPT-4-mini for headline clustering
• Create/merge event records
• Calculate event rankings (source count + recency)
• Trigger trading idea generation for top events

Dependencies:
• openai Python SDK
• SQLAlchemy (database access)
• Embeddings library (optional, for similarity matching)

Configuration:
• GPT-4-mini API key
• Batch size (default: 50 articles)
• Clustering prompt templates
• Event similarity threshold
• Top-N events for idea generation (default: 10)
```

#### **Trading Idea Generator Service**
```
src/services/trading_idea_generator.py

Responsibilities:
• Fetch top-ranked events
• Build context-rich prompts for GPT-4
• Generate trading ideas via LLM
• Parse and validate LLM responses
• Store trading ideas with metadata
• Notify subscribers of new ideas

Dependencies:
• openai Python SDK
• Prompt engineering templates
• SQLAlchemy (database access)

Configuration:
• GPT-4 API key
• Prompt templates
• Structured output schema
• Retry/error handling policies
```

### 4.2 Supporting Modules

#### **Database Models & Repositories**
```
src/models/
├── article.py          # Article ORM model
├── event.py            # Event ORM model
├── trading_idea.py     # TradingIdea ORM model
└── feed_metadata.py    # FeedMetadata ORM model

src/repositories/
├── article_repository.py
├── event_repository.py
├── trading_idea_repository.py
└── feed_repository.py

Pattern: Repository Pattern for data access abstraction
Benefits: Testability, swappable backends, clean separation
```

#### **API Layer**
```
src/api/
├── main.py                 # FastAPI app initialization
├── routes/
│   ├── feeds.py            # Feed management endpoints
│   ├── events.py           # Event browsing endpoints
│   ├── trading_ideas.py    # Trading ideas endpoints
│   └── dashboard.py        # Dashboard aggregation endpoint
├── websockets/
│   └── updates.py          # WebSocket handler for real-time updates
└── middleware/
    ├── error_handler.py    # Global error handling
    └── logging.py          # Request/response logging
```

#### **Frontend**
```
frontend/
├── public/
│   └── index.html          # Single-page app shell
├── src/
│   ├── components/
│   │   ├── Dashboard.js    # Overview dashboard
│   │   ├── EventsExplorer.js   # Event browsing interface
│   │   └── TradingIdeas.js     # Trading ideas display
│   ├── services/
│   │   ├── api.js          # API client
│   │   └── websocket.js    # WebSocket client
│   └── App.js              # Main app component
└── package.json

Framework: React (or Vue.js, or vanilla JS for ultra-lightweight MVP)
```

---

## 5. Technology Stack (MVP)

### 5.1 Backend Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Web Framework** | FastAPI | Async support, auto-docs, WebSocket support, minimal overhead |
| **Database** | SQLite | Zero-config, single-file, sufficient for MVP, easy backup |
| **ORM** | SQLAlchemy | Industry standard, supports SQLite, easy migrations |
| **Task Scheduler** | APScheduler | Lightweight, Python-native, no external dependencies |
| **HTTP Client** | httpx | Async HTTP, modern API, efficient connection pooling |
| **RSS Parser** | feedparser | Battle-tested, handles edge cases, widely used |
| **LLM Client** | openai (official SDK) | Reliable, well-maintained, supports GPT-4/mini |
| **Logging** | structlog | Structured logs, easy parsing, production-ready |
| **Testing** | pytest + pytest-asyncio | Standard Python testing, async support |

### 5.2 Frontend Stack (Minimal MVP)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Framework** | React (or vanilla JS) | React for scalability, vanilla for ultra-lightweight |
| **Build Tool** | Vite | Fast dev server, minimal config, small bundle |
| **HTTP Client** | fetch API | Native browser support, no extra dependencies |
| **Charts** | Chart.js | Lightweight, simple API, sufficient for MVP |
| **WebSocket** | Native WebSocket API | Built-in browser support |

### 5.3 Infrastructure

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Deployment** | Docker + docker-compose | Single-command deployment, consistent environments |
| **Process Manager** | uvicorn (built-in) | FastAPI-native, auto-reload in dev |
| **Reverse Proxy** | Nginx (optional) | Optional for production, static file serving |
| **Monitoring** | Structlog + file logs | Simple file-based logging, easily parseable |

---

## 6. Database Schema

### 6.1 Entity-Relationship Diagram

```
┌─────────────────────────────────────┐
│            ARTICLES                 │
├─────────────────────────────────────┤
│ id                 INTEGER PK       │
│ url                TEXT UNIQUE      │
│ title              TEXT             │
│ content            TEXT             │
│ summary            TEXT             │
│ published_at       DATETIME         │
│ fetched_at         DATETIME         │
│ source             TEXT             │
│ author             TEXT             │
│ event_id           INTEGER FK       │◄─────┐
│ created_at         DATETIME         │      │
└─────────────────────────────────────┘      │
                                              │
┌─────────────────────────────────────┐      │
│            EVENTS                   │      │
├─────────────────────────────────────┤      │
│ id                 INTEGER PK       │──────┘
│ name               TEXT             │
│ description        TEXT             │
│ article_count      INTEGER          │
│ source_count       INTEGER          │
│ earliest_at        DATETIME         │
│ latest_at          DATETIME         │
│ rank_score         FLOAT            │
│ has_trading_idea   BOOLEAN          │
│ created_at         DATETIME         │
│ updated_at         DATETIME         │
└─────────────────────────────────────┘
              │
              │
              ▼
┌─────────────────────────────────────┐
│         TRADING_IDEAS               │
├─────────────────────────────────────┤
│ id                 INTEGER PK       │
│ event_id           INTEGER FK       │
│ idea_text          TEXT             │
│ reasoning          TEXT             │
│ instruments        TEXT (JSON)      │
│ confidence         TEXT             │
│ timeframe          TEXT             │
│ created_at         DATETIME         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         FEED_METADATA               │
├─────────────────────────────────────┤
│ id                 INTEGER PK       │
│ feed_url           TEXT UNIQUE      │
│ feed_name          TEXT             │
│ last_fetch_at      DATETIME         │
│ last_success_at    DATETIME         │
│ article_count      INTEGER          │
│ avg_articles_per_hour FLOAT         │
│ next_refresh_at    DATETIME         │
│ is_active          BOOLEAN          │
│ error_count        INTEGER          │
│ last_error         TEXT             │
└─────────────────────────────────────┘
```

### 6.2 Key Indexes

```sql
-- Articles
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_event_id ON articles(event_id);
CREATE INDEX idx_articles_source ON articles(source);
CREATE UNIQUE INDEX idx_articles_url ON articles(url);

-- Events
CREATE INDEX idx_events_rank_score ON events(rank_score DESC);
CREATE INDEX idx_events_latest_at ON events(latest_at DESC);
CREATE INDEX idx_events_has_idea ON events(has_trading_idea);

-- Trading Ideas
CREATE INDEX idx_ideas_event_id ON trading_ideas(event_id);
CREATE INDEX idx_ideas_created_at ON trading_ideas(created_at DESC);

-- Feed Metadata
CREATE INDEX idx_feeds_next_refresh ON feed_metadata(next_refresh_at);
CREATE INDEX idx_feeds_active ON feed_metadata(is_active);
```

---

## 7. API Contracts

### 7.1 REST Endpoints

#### **GET /api/feeds**
```json
Response:
{
  "feeds": [
    {
      "id": 1,
      "name": "Reuters Business",
      "url": "https://reuters.com/finance/rss",
      "last_fetch": "2025-10-22T14:30:00Z",
      "article_count": 1250,
      "is_active": true,
      "next_refresh": "2025-10-22T14:45:00Z"
    }
  ]
}
```

#### **POST /api/feeds/refresh**
```json
Request:
{
  "feed_ids": [1, 2],  // Optional: specific feeds, or all if omitted
  "force": false       // Optional: ignore adaptive timing
}

Response:
{
  "status": "triggered",
  "feeds_refreshed": 2,
  "new_articles": 15
}
```

#### **GET /api/events?limit=50&offset=0&sort=rank**
```json
Response:
{
  "events": [
    {
      "id": 123,
      "name": "Federal Reserve Rate Decision",
      "description": "FOMC announces interest rate policy",
      "article_count": 45,
      "source_count": 12,
      "latest_at": "2025-10-22T14:00:00Z",
      "rank_score": 125.8,
      "has_trading_idea": true
    }
  ],
  "total": 250,
  "limit": 50,
  "offset": 0
}
```

#### **GET /api/events/{event_id}**
```json
Response:
{
  "id": 123,
  "name": "Federal Reserve Rate Decision",
  "description": "FOMC announces interest rate policy...",
  "article_count": 45,
  "source_count": 12,
  "earliest_at": "2025-10-22T10:00:00Z",
  "latest_at": "2025-10-22T14:00:00Z",
  "rank_score": 125.8,
  "articles": [
    {
      "id": 5001,
      "title": "Fed Holds Rates Steady",
      "url": "https://...",
      "source": "Reuters",
      "published_at": "2025-10-22T14:00:00Z"
    }
  ],
  "trading_idea": {
    "id": 42,
    "idea_text": "Consider long USD positions...",
    "reasoning": "Rate decision signals...",
    "instruments": ["EUR/USD", "US10Y"],
    "confidence": "high",
    "timeframe": "1-3 days"
  }
}
```

#### **GET /api/trading-ideas?limit=10**
```json
Response:
{
  "ideas": [
    {
      "id": 42,
      "event": {
        "id": 123,
        "name": "Federal Reserve Rate Decision"
      },
      "idea_text": "Consider long USD positions against EUR and JPY",
      "reasoning": "Rate decision signals continued hawkish stance...",
      "instruments": ["EUR/USD", "USD/JPY", "US10Y"],
      "confidence": "high",
      "timeframe": "1-3 days",
      "created_at": "2025-10-22T14:30:00Z"
    }
  ]
}
```

#### **GET /api/dashboard**
```json
Response:
{
  "stats": {
    "total_articles": 15420,
    "total_events": 342,
    "total_ideas": 85,
    "articles_last_24h": 245,
    "events_last_24h": 18,
    "active_feeds": 8
  },
  "recent_events": [...],  // Top 5 by rank
  "recent_ideas": [...]     // Top 5 by created_at
}
```

### 7.2 WebSocket Protocol

#### **Connection: ws://host/ws/updates**

**Client → Server (Subscribe):**
```json
{
  "action": "subscribe",
  "channels": ["articles", "events", "ideas"]
}
```

**Server → Client (Updates):**
```json
{
  "channel": "events",
  "type": "new_event",
  "data": {
    "id": 344,
    "name": "Oil Price Spike",
    "article_count": 3,
    "rank_score": 45.2
  }
}

{
  "channel": "ideas",
  "type": "new_idea",
  "data": {
    "id": 86,
    "event_id": 123,
    "idea_text": "...",
    "confidence": "medium"
  }
}
```

---

## 8. Scalability Considerations

### 8.1 MVP → Production Evolution Path

| Aspect | MVP (Phase 1) | Scale-Up (Phase 2) | Enterprise (Phase 3) |
|--------|--------------|-------------------|---------------------|
| **Database** | SQLite (single file) | PostgreSQL (managed) | PostgreSQL + read replicas |
| **Task Queue** | APScheduler (in-process) | Celery + Redis | Celery + Redis cluster |
| **Caching** | None | Redis (simple cache) | Redis + CDN |
| **Load Balancing** | Single instance | Nginx → 2-3 instances | Load balancer → auto-scale |
| **File Storage** | Local disk | S3-compatible object storage | Multi-region object storage |
| **Monitoring** | File logs | Prometheus + Grafana | Full observability stack |
| **Deployment** | Single Docker container | Docker Compose | Kubernetes |

### 8.2 Horizontal Scaling Strategy

**Stateless Services (easily scaled):**
- API servers (FastAPI instances)
- Feed ingestion workers
- Event clustering workers
- Trading idea generators

**Stateful Components (require coordination):**
- SQLite → PostgreSQL migration required
- APScheduler → Celery with Redis broker
- WebSocket connections → sticky sessions or Redis pub/sub

### 8.3 Performance Bottlenecks & Mitigations

| Bottleneck | Detection | Mitigation (MVP) | Mitigation (Scale) |
|-----------|-----------|-----------------|-------------------|
| **LLM API Rate Limits** | 429 errors | Exponential backoff | Request queuing + batching |
| **Database Writes** | Slow inserts | Batch inserts | Connection pooling + sharding |
| **RSS Fetch Latency** | Slow refreshes | Async fetching | Distributed workers |
| **Event Clustering Cost** | High API bills | Batch articles | Caching + embeddings |
| **WebSocket Connections** | Memory usage | Limit connections | Redis pub/sub broadcast |

---

## 9. Error Handling Strategy

### 9.1 Error Categories & Responses

#### **External API Failures (RSS feeds, OpenAI)**
```python
Strategy:
• Exponential backoff with jitter
• Circuit breaker pattern (fail-fast after N failures)
• Fallback to cached data (stale-while-revalidate)
• Log errors with full context
• Alert on repeated failures

Example:
try:
    response = await openai_client.chat.completions.create(...)
except openai.RateLimitError:
    # Backoff and retry
    await asyncio.sleep(exponential_backoff(attempt))
except openai.APIError as e:
    # Log and continue with next batch
    logger.error("OpenAI API error", error=str(e), batch_id=batch_id)
```

#### **Database Errors**
```python
Strategy:
• Transaction rollback on failure
• Retry transient errors (locked database)
• Fail-fast on schema errors
• Log with query context

Example:
try:
    async with db.transaction():
        await db.execute(insert_query)
except SQLAlchemyError as e:
    await db.rollback()
    logger.error("Database error", query=query, error=str(e))
    raise
```

#### **Data Validation Errors**
```python
Strategy:
• Validate early (Pydantic models)
• Skip invalid items, continue batch
• Log validation errors for debugging
• Surface validation stats in monitoring

Example:
for article in articles:
    try:
        validated = ArticleSchema(**article)
        await save_article(validated)
    except ValidationError as e:
        logger.warning("Invalid article", error=e, article=article)
        continue  # Skip this article
```

### 9.2 Health Checks

```python
# /health endpoint
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5
    },
    "openai_api": {
      "status": "up",
      "last_request": "2025-10-22T14:30:00Z"
    },
    "scheduler": {
      "status": "running",
      "pending_jobs": 3
    }
  },
  "timestamp": "2025-10-22T14:35:00Z"
}
```

---

## 10. Security Considerations

### 10.1 API Security (MVP)

| Concern | Mitigation |
|---------|-----------|
| **API Key Exposure** | Environment variables, never commit to git |
| **CORS** | Restrict origins in FastAPI CORS middleware |
| **Rate Limiting** | Simple in-memory rate limiter (10 req/sec per IP) |
| **Input Validation** | Pydantic models for all inputs |
| **SQL Injection** | ORM (SQLAlchemy) with parameterized queries |

### 10.2 Data Privacy

- No PII collection (news articles are public)
- API keys stored in environment variables
- Database file permissions: 600 (owner read/write only)

---

## 11. Deployment Architecture

### 11.1 Single-Container Deployment (MVP)

```
┌──────────────────────────────────────────────────────────┐
│                   DOCKER CONTAINER                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (uvicorn)                     │  │
│  │  • API endpoints                                   │  │
│  │  • WebSocket server                                │  │
│  │  • Background task scheduler (APScheduler)         │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  SQLite Database File                              │  │
│  │  /data/news_trading.db                             │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Static Frontend Files                             │  │
│  │  /app/frontend/dist                                │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                       │
                       │ Port 8000
                       ▼
                  User Browser
```

### 11.2 Docker Compose Configuration

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data  # SQLite database persistence
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///data/news_trading.db
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 11.3 Resource Requirements (MVP)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 1 core | 2 cores |
| **RAM** | 512 MB | 1 GB |
| **Disk** | 1 GB | 5 GB (includes logs) |
| **Network** | 10 Mbps | 50 Mbps |

**Estimated Costs:**
- Cloud VM (AWS t3.small): ~$15/month
- OpenAI API (GPT-4-mini + GPT-4): ~$20-50/month (depends on volume)
- **Total**: ~$35-65/month

---

## 12. Architecture Decision Records (ADRs)

### ADR-001: Use SQLite for MVP Database

**Context:** Need persistent storage for articles, events, and trading ideas.

**Decision:** Use SQLite instead of PostgreSQL for MVP.

**Rationale:**
- Zero configuration (no separate database server)
- Single-file database (easy backup/restore)
- Sufficient performance for MVP (<1000 articles/day)
- Easy migration path to PostgreSQL when needed
- Built-in to Python (no extra dependencies)

**Consequences:**
- **Positive:** Fastest MVP deployment, minimal ops overhead
- **Negative:** Limited concurrent writes, no horizontal scaling
- **Mitigation:** Plan PostgreSQL migration when article rate exceeds 1000/day

---

### ADR-002: Use APScheduler Instead of Celery

**Context:** Need scheduled task execution for feed refreshes.

**Decision:** Use APScheduler (in-process) instead of Celery (distributed).

**Rationale:**
- No external broker required (Redis/RabbitMQ)
- Simpler deployment (single container)
- Sufficient for MVP (predictable, periodic tasks)
- Less operational complexity

**Consequences:**
- **Positive:** Faster MVP, fewer moving parts
- **Negative:** Cannot distribute tasks across workers
- **Mitigation:** Migrate to Celery when task volume requires distribution

---

### ADR-003: GPT-4-mini for Clustering, GPT-4 for Ideas

**Context:** Balance cost and quality for LLM operations.

**Decision:** Use GPT-4-mini for article clustering, GPT-4 for trading ideas.

**Rationale:**
- Clustering is high-volume (all articles), lower complexity
- Trading ideas are low-volume (top 10 events), require higher quality
- Cost optimization: GPT-4-mini is 10x cheaper
- Quality balance: Ideas are user-facing, clustering is internal

**Consequences:**
- **Positive:** 70% cost reduction vs. all-GPT-4
- **Negative:** Potential clustering quality issues
- **Mitigation:** Monitor clustering accuracy, adjust prompts

---

### ADR-004: Adaptive Refresh Intervals

**Context:** Balance freshness vs. API rate limits and costs.

**Decision:** Calculate refresh intervals as `min(time_for_5_articles, 15_min)`.

**Rationale:**
- High-volume feeds refresh faster (more news = faster updates)
- Low-volume feeds don't waste API calls
- 15-min cap prevents excessive polling
- 5-article threshold ensures meaningful batches for clustering

**Consequences:**
- **Positive:** Efficient API usage, responsive to news velocity
- **Negative:** Complex scheduling logic
- **Mitigation:** Log refresh decisions for debugging

---

### ADR-005: WebSocket for Real-Time Updates

**Context:** Users want real-time notifications of new events/ideas.

**Decision:** Use WebSocket (FastAPI built-in) instead of polling.

**Rationale:**
- Lower latency (instant updates vs. polling interval)
- Reduced server load (no repeated HTTP requests)
- Better UX (real-time feel)
- FastAPI has native WebSocket support

**Consequences:**
- **Positive:** Superior UX, efficient use of bandwidth
- **Negative:** Connection state management complexity
- **Mitigation:** Implement reconnection logic, heartbeat pings

---

## 13. Future Enhancements (Post-MVP)

### Phase 2: Enhanced Features
- **Historical Analysis**: Store and analyze past trading ideas performance
- **Sentiment Analysis**: Add sentiment scoring to events
- **Custom Feeds**: User-defined RSS feed management
- **Filtering**: Filter events by sector, asset class, geography
- **Email Alerts**: Notify users of high-priority ideas

### Phase 3: Advanced Capabilities
- **Backtesting**: Simulate trading ideas against historical data
- **Portfolio Integration**: Connect to brokerage APIs
- **Multi-LLM Support**: Compare ideas from different models
- **Social Media Integration**: Incorporate Twitter/Reddit signals
- **Collaborative Features**: Share and discuss ideas with team

---

## 14. Monitoring & Observability

### 14.1 Key Metrics to Track

**Application Metrics:**
- Articles ingested per hour
- Events created per day
- Trading ideas generated per day
- API response times (p50, p95, p99)
- WebSocket connection count
- Background job success/failure rate

**LLM Metrics:**
- OpenAI API call count (by model)
- Token usage (by operation type)
- API error rate
- Cost per day (estimated)

**System Metrics:**
- Database file size
- CPU/Memory usage
- Disk I/O
- Network bandwidth

### 14.2 Logging Structure

```json
{
  "timestamp": "2025-10-22T14:30:00Z",
  "level": "INFO",
  "service": "feed_ingestion",
  "event": "feed_refreshed",
  "feed_url": "https://reuters.com/rss",
  "new_articles": 15,
  "duration_ms": 2340,
  "trace_id": "abc123"
}
```

---

## 15. Testing Strategy

### 15.1 Test Pyramid

```
        ┌───────────────┐
        │  E2E Tests    │  ← 5% (critical user flows)
        │   (Playwright)│
        └───────────────┘
       ┌─────────────────┐
       │ Integration     │  ← 25% (API + DB)
       │ Tests (pytest)  │
       └─────────────────┘
    ┌──────────────────────┐
    │  Unit Tests          │  ← 70% (business logic)
    │  (pytest)            │
    └──────────────────────┘
```

### 15.2 Test Coverage Targets

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| **Feed Ingestion** | 85% | Deduplication, adaptive scheduling |
| **Event Clustering** | 80% | LLM response parsing, event merging |
| **Trading Ideas** | 85% | Prompt building, response validation |
| **API Endpoints** | 90% | All endpoints, error cases |
| **Database Layer** | 75% | CRUD operations, transactions |

---

## Conclusion

This architecture provides a **solid foundation for rapid MVP development** while maintaining **clear paths to scalability**. The design prioritizes:

1. **Simplicity**: Single-container deployment, minimal dependencies
2. **Efficiency**: Adaptive refresh intervals, batched LLM calls, cost optimization
3. **Maintainability**: Clean separation of concerns, repository pattern, structured logging
4. **Scalability**: Clear migration paths to distributed systems (PostgreSQL, Celery, K8s)

**Next Steps:**
1. Review and approve architecture
2. Create detailed API specifications
3. Design database schema with migrations
4. Implement core services (feed ingestion → clustering → ideas)
5. Build minimal frontend for testing
6. Deploy MVP and gather feedback

**Estimated Timeline:**
- Architecture Review: 1 day
- Backend Implementation: 5-7 days
- Frontend Implementation: 3-4 days
- Testing & Deployment: 2-3 days
- **Total MVP**: 2-3 weeks

---

**Document Control:**
- **Version**: 1.0.0
- **Last Updated**: 2025-10-22
- **Status**: Draft for Review
- **Next Review**: After stakeholder approval
