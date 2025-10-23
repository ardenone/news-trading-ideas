# RSS Feed Ingestion and Queue System Design

## Executive Summary

This document outlines the architecture for a high-performance, adaptive RSS feed ingestion system that dynamically adjusts polling intervals based on source publishing velocity. The system is designed for MVP deployment with minimal dependencies while maintaining scalability for future growth.

## Technology Stack Recommendation

### Core Runtime: **Python 3.11+ with asyncio**

**Rationale:**
- Native async/await support for I/O-bound operations
- Rich ecosystem for RSS parsing and data processing
- SQLite native support with aiosqlite for async operations
- Easier deployment and maintenance for MVP

**Key Libraries:**
- `feedparser` (v6.0+) - Battle-tested RSS/Atom parser
- `aiohttp` - Async HTTP client for feed fetching
- `aiosqlite` - Async SQLite wrapper
- `apscheduler` - Advanced Python scheduler with async support
- `pydantic` - Data validation and settings management
- `structlog` - Structured logging

**Alternative (Node.js):**
- If team has stronger Node.js expertise
- Libraries: `rss-parser`, `node-cron`, `better-sqlite3`

---

## 1. System Architecture

### 1.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Ingestion Orchestrator                    │
│  - Feed registry management                                  │
│  - Adaptive scheduling coordination                          │
│  - Health monitoring                                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────────────┐
             │                                                  │
┌────────────▼──────────┐                    ┌─────────────────▼─────────┐
│  Feed Fetcher Pool    │                    │  Adaptive Queue Manager   │
│  - Async HTTP client  │                    │  - Velocity tracking      │
│  - Retry logic        │                    │  - Priority calculation   │
│  - Timeout handling   │                    │  - Schedule optimization  │
└────────────┬──────────┘                    └─────────────────┬─────────┘
             │                                                  │
             │                                                  │
┌────────────▼──────────────────────────────────────────────────▼─────────┐
│                        RSS Parser & Deduplicator                         │
│  - XML parsing                                                           │
│  - Content normalization                                                 │
│  - Hash-based deduplication                                              │
│  - Metadata extraction                                                   │
└────────────┬─────────────────────────────────────────────────────────────┘
             │
┌────────────▼──────────┐
│  Article Processor    │
│  - Batch insertion    │
│  - Event triggering   │
│  - Error recovery     │
└────────────┬──────────┘
             │
┌────────────▼──────────┐         ┌─────────────────────────────┐
│  SQLite Database      │────────▶│  Event Pipeline Triggers    │
│  - articles table     │         │  - Headline grouping        │
│  - feed_stats table   │         │  - Trading ideas generation │
│  - dedup_cache table  │         └─────────────────────────────┘
└───────────────────────┘
```

### 1.2 Data Flow

```
1. Orchestrator schedules feed fetch based on adaptive queue priorities
2. Fetcher pool retrieves RSS feed asynchronously (with timeout)
3. Parser extracts articles and checks deduplication cache
4. Processor batches new articles and inserts to database
5. Statistics updater recalculates feed velocity metrics
6. Queue manager updates next fetch time for the feed
7. Event triggers fire for downstream processing
```

---

## 2. Component Specifications

### 2.1 Feed Fetcher Pool

**Responsibility:** Asynchronously fetch RSS feeds with resilience patterns

**Key Features:**
- Concurrent feed fetching (configurable parallelism)
- Exponential backoff retry logic
- Request timeout enforcement (10s default)
- User-Agent rotation to avoid blocking
- ETag/Last-Modified caching for bandwidth optimization

**Pseudocode:**

```python
class FeedFetcher:
    def __init__(self, max_concurrent: int = 10, timeout: int = 10):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers={'User-Agent': 'NewsAggregator/1.0'}
        )
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_feed(self, feed_url: str, etag: str = None) -> FeedResponse:
        """
        Fetch RSS feed with conditional GET support

        Returns:
            FeedResponse with status, content, updated etag
        """
        async with self.semaphore:
            headers = {}
            if etag:
                headers['If-None-Match'] = etag

            for attempt in range(3):  # Max 3 retries
                try:
                    async with self.session.get(feed_url, headers=headers) as response:
                        if response.status == 304:  # Not Modified
                            return FeedResponse(status=304, articles=[])

                        if response.status == 200:
                            content = await response.text()
                            new_etag = response.headers.get('ETag')
                            return FeedResponse(
                                status=200,
                                content=content,
                                etag=new_etag
                            )

                        # Handle 4xx/5xx errors
                        await self._log_error(feed_url, response.status)
                        return FeedResponse(status=response.status, error=True)

                except asyncio.TimeoutError:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue

                except Exception as e:
                    await self._log_exception(feed_url, e)
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        return FeedResponse(status=0, error=True, exception=str(e))
```

**Configuration Parameters:**
```yaml
fetcher:
  max_concurrent_requests: 10
  request_timeout_seconds: 10
  retry_attempts: 3
  retry_backoff_base: 2
  user_agent: "NewsAggregator/1.0 (contact@example.com)"
```

---

### 2.2 RSS Parser & Deduplicator

**Responsibility:** Parse RSS/Atom feeds and identify unique articles

**Key Features:**
- Support for RSS 2.0, RSS 1.0, and Atom formats
- Robust datetime parsing (multiple format support)
- Content hash deduplication (URL + publish_datetime)
- Fallback extraction for missing fields

**Pseudocode:**

```python
import feedparser
import hashlib
from datetime import datetime
from typing import List, Optional

class RSSParser:
    def __init__(self, db_connection):
        self.db = db_connection
        self.dedup_cache = LRUCache(maxsize=10000)  # In-memory cache

    async def parse_feed(self, content: str, source_name: str) -> List[Article]:
        """
        Parse RSS XML and extract articles with deduplication

        Returns:
            List of unique Article objects
        """
        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries:
            # Extract fields with fallbacks
            article = self._extract_article(entry, source_name)

            # Skip if deduplication fails
            if not await self._is_unique(article):
                continue

            articles.append(article)

        return articles

    def _extract_article(self, entry, source_name: str) -> Article:
        """Extract and normalize article fields"""
        # URL (required)
        url = entry.get('link') or entry.get('id')
        if not url:
            raise ValueError("Article missing required URL")

        # Headline (required)
        headline = entry.get('title', '').strip()
        if not headline:
            raise ValueError("Article missing required headline")

        # Publish datetime with multiple format support
        publish_datetime = self._parse_datetime(
            entry.get('published') or
            entry.get('updated') or
            entry.get('pubDate')
        )

        # Use current time as fallback (rare case)
        if not publish_datetime:
            publish_datetime = datetime.utcnow()

        return Article(
            url=url,
            headline=headline,
            source=source_name,
            publish_datetime=publish_datetime,
            raw_content=entry.get('summary', '')
        )

    def _parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Parse datetime with multiple format support"""
        if not date_string:
            return None

        # feedparser handles most formats automatically
        parsed = feedparser._parse_date(date_string)
        if parsed:
            return datetime(*parsed[:6])

        # Fallback manual parsing for edge cases
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        return None

    async def _is_unique(self, article: Article) -> bool:
        """Check if article is unique using hash-based deduplication"""
        # Generate content hash (URL + publish_datetime)
        content_hash = hashlib.sha256(
            f"{article.url}|{article.publish_datetime.isoformat()}".encode()
        ).hexdigest()

        # Check in-memory cache first (fast path)
        if content_hash in self.dedup_cache:
            return False

        # Check database (slower, but persistent)
        exists = await self.db.execute(
            "SELECT 1 FROM dedup_cache WHERE content_hash = ? LIMIT 1",
            (content_hash,)
        )

        if exists:
            self.dedup_cache[content_hash] = True
            return False

        # Store in cache and database
        self.dedup_cache[content_hash] = True
        await self.db.execute(
            "INSERT INTO dedup_cache (content_hash, created_at) VALUES (?, ?)",
            (content_hash, datetime.utcnow())
        )

        return True
```

**Database Schema:**

```sql
-- Deduplication cache table
CREATE TABLE IF NOT EXISTS dedup_cache (
    content_hash TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP GENERATED ALWAYS AS (
        datetime(created_at, '+7 days')
    ) STORED
);

CREATE INDEX idx_dedup_expires ON dedup_cache(expires_at);

-- Cleanup old entries periodically
-- DELETE FROM dedup_cache WHERE expires_at < datetime('now');
```

---

### 2.3 Adaptive Queue Manager

**Responsibility:** Calculate optimal next fetch time based on feed velocity

**Key Algorithm:**

```
next_refresh_time = min(
    time_for_5_new_articles_based_on_historical_rate,
    15_minutes  # Maximum refresh interval
)

Minimum refresh interval: 1 minute (to avoid hammering sources)
```

**Velocity Tracking:**

The system tracks:
- Average articles per hour (rolling 24h window)
- Peak publishing times (hourly histogram)
- Decay factor for aging statistics

**Pseudocode:**

```python
from datetime import datetime, timedelta
from typing import Optional

class AdaptiveQueueManager:
    MIN_REFRESH_INTERVAL = timedelta(minutes=1)
    MAX_REFRESH_INTERVAL = timedelta(minutes=15)
    TARGET_ARTICLES_PER_FETCH = 5

    def __init__(self, db_connection):
        self.db = db_connection

    async def calculate_next_fetch(self, feed_id: str) -> datetime:
        """
        Calculate optimal next fetch time based on feed velocity

        Algorithm:
        1. Get historical publishing rate (articles/hour)
        2. Calculate time needed for ~5 new articles
        3. Clamp between MIN and MAX refresh intervals
        4. Return next scheduled fetch time
        """
        stats = await self._get_feed_stats(feed_id)

        if not stats or stats.articles_per_hour == 0:
            # No historical data - use conservative 15min interval
            return datetime.utcnow() + self.MAX_REFRESH_INTERVAL

        # Calculate time for TARGET_ARTICLES_PER_FETCH articles
        hours_per_target = self.TARGET_ARTICLES_PER_FETCH / stats.articles_per_hour
        interval = timedelta(hours=hours_per_target)

        # Apply bounds
        interval = max(interval, self.MIN_REFRESH_INTERVAL)
        interval = min(interval, self.MAX_REFRESH_INTERVAL)

        # Account for peak publishing times (optional optimization)
        if stats.current_hour_multiplier > 1.5:
            # This is a high-activity hour - check more frequently
            interval = interval * 0.7

        next_fetch = datetime.utcnow() + interval

        # Update feed schedule in database
        await self._update_feed_schedule(feed_id, next_fetch)

        return next_fetch

    async def update_feed_stats(self, feed_id: str, new_articles_count: int):
        """Update velocity statistics after successful fetch"""
        stats = await self._get_feed_stats(feed_id) or FeedStats(feed_id)

        # Update rolling average (exponential moving average)
        decay = 0.9  # Weight toward recent history
        current_rate = new_articles_count  # Articles in last fetch interval

        stats.articles_per_hour = (
            decay * stats.articles_per_hour +
            (1 - decay) * current_rate
        )

        # Update hourly histogram
        current_hour = datetime.utcnow().hour
        stats.hourly_distribution[current_hour] += new_articles_count

        # Calculate peak hour multiplier
        avg_hourly = sum(stats.hourly_distribution) / 24
        stats.current_hour_multiplier = (
            stats.hourly_distribution[current_hour] / avg_hourly
            if avg_hourly > 0 else 1.0
        )

        # Persist to database
        await self._save_feed_stats(stats)

    async def get_priority_queue(self, limit: int = 10) -> List[FeedSchedule]:
        """Get next feeds to fetch, ordered by priority"""
        query = """
            SELECT feed_id, feed_url, next_fetch_time, priority_score
            FROM feed_schedules
            WHERE next_fetch_time <= ?
            ORDER BY priority_score DESC, next_fetch_time ASC
            LIMIT ?
        """

        feeds = await self.db.execute_all(
            query,
            (datetime.utcnow(), limit)
        )

        return [FeedSchedule(**feed) for feed in feeds]

    async def _get_feed_stats(self, feed_id: str) -> Optional[FeedStats]:
        """Retrieve historical statistics for feed"""
        result = await self.db.execute_one(
            """
            SELECT
                feed_id,
                articles_per_hour,
                hourly_distribution,
                last_fetch_time,
                total_articles_fetched,
                consecutive_errors
            FROM feed_stats
            WHERE feed_id = ?
            """,
            (feed_id,)
        )

        return FeedStats(**result) if result else None
```

**Database Schema:**

```sql
-- Feed scheduling table
CREATE TABLE IF NOT EXISTS feed_schedules (
    feed_id TEXT PRIMARY KEY,
    feed_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    next_fetch_time TIMESTAMP NOT NULL,
    priority_score REAL DEFAULT 1.0,
    enabled BOOLEAN DEFAULT 1,
    etag TEXT,
    last_modified TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_next_fetch ON feed_schedules(next_fetch_time, priority_score);

-- Feed statistics table
CREATE TABLE IF NOT EXISTS feed_stats (
    feed_id TEXT PRIMARY KEY,
    articles_per_hour REAL DEFAULT 0.0,
    hourly_distribution TEXT,  -- JSON array of 24 integers
    last_fetch_time TIMESTAMP,
    last_successful_fetch TIMESTAMP,
    total_articles_fetched INTEGER DEFAULT 0,
    consecutive_errors INTEGER DEFAULT 0,
    avg_articles_per_fetch REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2.4 Article Processor

**Responsibility:** Batch insert articles and trigger downstream events

**Key Features:**
- Batch insertion for performance (configurable batch size)
- Transaction safety with rollback
- Event emission for downstream processing
- Backpressure handling

**Pseudocode:**

```python
class ArticleProcessor:
    BATCH_SIZE = 100

    def __init__(self, db_connection, event_emitter):
        self.db = db_connection
        self.events = event_emitter

    async def process_articles(
        self,
        articles: List[Article],
        feed_id: str
    ) -> ProcessingResult:
        """
        Batch insert articles and trigger events

        Returns:
            ProcessingResult with counts and event status
        """
        if not articles:
            return ProcessingResult(inserted=0, triggered_events=0)

        inserted_count = 0

        # Process in batches for large feeds
        for batch in self._chunk(articles, self.BATCH_SIZE):
            try:
                # Use transaction for atomicity
                async with self.db.transaction():
                    batch_ids = await self._insert_batch(batch)
                    inserted_count += len(batch_ids)

                    # Trigger headline grouping event
                    await self.events.emit('articles.new', {
                        'feed_id': feed_id,
                        'article_ids': batch_ids,
                        'count': len(batch_ids)
                    })

            except Exception as e:
                # Log error but continue processing next batch
                await self._log_batch_error(feed_id, batch, e)

        return ProcessingResult(
            inserted=inserted_count,
            triggered_events=1 if inserted_count > 0 else 0
        )

    async def _insert_batch(self, articles: List[Article]) -> List[str]:
        """Insert batch of articles and return IDs"""
        query = """
            INSERT INTO articles (
                url, headline, source, publish_datetime,
                raw_content, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
        """

        values = [
            (
                article.url,
                article.headline,
                article.source,
                article.publish_datetime,
                article.raw_content,
                datetime.utcnow()
            )
            for article in articles
        ]

        results = await self.db.executemany(query, values)
        return [row['id'] for row in results]

    def _chunk(self, items: List, size: int):
        """Split list into chunks of specified size"""
        for i in range(0, len(items), size):
            yield items[i:i + size]
```

---

### 2.5 Ingestion Orchestrator

**Responsibility:** Main event loop coordinating all components

**Pseudocode:**

```python
class IngestionOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.fetcher = FeedFetcher(
            max_concurrent=config.max_concurrent_fetches
        )
        self.parser = RSSParser(db_connection)
        self.processor = ArticleProcessor(db_connection, event_emitter)
        self.queue_manager = AdaptiveQueueManager(db_connection)
        self.scheduler = APScheduler()
        self.running = False

    async def start(self):
        """Start the ingestion service"""
        self.running = True

        # Start scheduler with periodic checks
        self.scheduler.add_job(
            self._fetch_cycle,
            'interval',
            seconds=30,  # Check every 30 seconds
            id='fetch_cycle'
        )

        # Start cleanup jobs
        self.scheduler.add_job(
            self._cleanup_dedup_cache,
            'interval',
            hours=1,
            id='cleanup_dedup'
        )

        self.scheduler.start()

        # Keep service running
        while self.running:
            await asyncio.sleep(1)

    async def _fetch_cycle(self):
        """Single fetch cycle - processes multiple feeds in parallel"""
        # Get feeds due for fetching
        feeds = await self.queue_manager.get_priority_queue(
            limit=self.config.max_concurrent_fetches
        )

        if not feeds:
            return  # Nothing to fetch

        # Fetch all feeds concurrently
        tasks = [
            self._process_feed(feed)
            for feed in feeds
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors
        for feed, result in zip(feeds, results):
            if isinstance(result, Exception):
                await self._handle_feed_error(feed, result)

    async def _process_feed(self, feed: FeedSchedule):
        """Complete processing pipeline for a single feed"""
        # 1. Fetch feed
        response = await self.fetcher.fetch_feed(
            feed.feed_url,
            etag=feed.etag
        )

        if response.error:
            await self._increment_error_count(feed.feed_id)
            return

        if response.status == 304:
            # No new content - still update schedule
            await self.queue_manager.calculate_next_fetch(feed.feed_id)
            return

        # 2. Parse articles
        articles = await self.parser.parse_feed(
            response.content,
            feed.source_name
        )

        # 3. Process and insert
        result = await self.processor.process_articles(
            articles,
            feed.feed_id
        )

        # 4. Update statistics and schedule
        await self.queue_manager.update_feed_stats(
            feed.feed_id,
            result.inserted
        )

        await self.queue_manager.calculate_next_fetch(feed.feed_id)

        # 5. Update ETag for next fetch
        if response.etag:
            await self._update_feed_etag(feed.feed_id, response.etag)

    async def stop(self):
        """Graceful shutdown"""
        self.running = False
        self.scheduler.shutdown(wait=True)
        await self.fetcher.close()
```

---

## 3. Event Pipeline Integration

### 3.1 Event Types

```python
# Event emitted when new articles are inserted
EVENT_NEW_ARTICLES = 'articles.new'
# Payload: { feed_id, article_ids, count }

# Event emitted when headline grouping should run
EVENT_TRIGGER_GROUPING = 'processing.group_headlines'
# Payload: { article_ids, trigger_reason }

# Event emitted when trading ideas should be generated
EVENT_TRIGGER_IDEAS = 'processing.generate_ideas'
# Payload: { event_ids, trigger_reason }
```

### 3.2 Event Handlers

```python
class EventPipeline:
    async def on_new_articles(self, payload):
        """Triggered when articles are inserted"""
        # Check if we should trigger headline grouping
        threshold = self.config.grouping_threshold  # e.g., 10 articles

        recent_ungrouped = await self.db.execute_one(
            "SELECT COUNT(*) FROM articles WHERE event_id IS NULL"
        )

        if recent_ungrouped >= threshold:
            await self.events.emit(EVENT_TRIGGER_GROUPING, {
                'trigger_reason': 'threshold_reached',
                'ungrouped_count': recent_ungrouped
            })

    async def on_events_updated(self, payload):
        """Triggered when events are updated"""
        # Generate trading ideas for updated events
        await self.events.emit(EVENT_TRIGGER_IDEAS, {
            'event_ids': payload['event_ids'],
            'trigger_reason': 'events_updated'
        })
```

---

## 4. Configuration Management

### 4.1 Configuration Schema

```yaml
# config/ingestion.yaml

ingestion:
  # Fetcher settings
  fetcher:
    max_concurrent_requests: 10
    request_timeout_seconds: 10
    retry_attempts: 3
    user_agent: "NewsAggregator/1.0"

  # Scheduler settings
  scheduler:
    fetch_cycle_interval_seconds: 30
    min_refresh_interval_minutes: 1
    max_refresh_interval_minutes: 15
    target_articles_per_fetch: 5

  # Parser settings
  parser:
    dedup_cache_size: 10000
    dedup_retention_days: 7

  # Processor settings
  processor:
    batch_size: 100
    max_queue_size: 1000

  # Event thresholds
  events:
    grouping_threshold_articles: 10
    grouping_interval_minutes: 5

  # Monitoring
  monitoring:
    metrics_port: 9090
    log_level: "INFO"
    structured_logging: true

# Feed sources configuration
feeds:
  - id: "reuters-world"
    url: "https://www.reuters.com/rssFeed/worldNews"
    source_name: "Reuters"
    priority: 1.0
    enabled: true

  - id: "bloomberg-markets"
    url: "https://www.bloomberg.com/feed/markets.rss"
    source_name: "Bloomberg"
    priority: 1.2
    enabled: true

  - id: "cnbc-breaking"
    url: "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    source_name: "CNBC"
    priority: 1.5
    enabled: true
```

### 4.2 Environment Variables

```bash
# .env file
DATABASE_PATH=/data/news_trading.db
REDIS_URL=redis://localhost:6379  # Optional for distributed setup
LOG_LEVEL=INFO
METRICS_ENABLED=true
SENTRY_DSN=  # Optional error tracking
```

---

## 5. Monitoring & Observability

### 5.1 Key Metrics

**Performance Metrics:**
- `feed_fetch_duration_seconds` (histogram) - Time to fetch each feed
- `articles_parsed_total` (counter) - Total articles parsed
- `articles_deduplicated_total` (counter) - Duplicate articles detected
- `articles_inserted_total` (counter) - Successfully inserted articles
- `feed_fetch_errors_total` (counter) - Failed fetch attempts

**Queue Metrics:**
- `queue_size` (gauge) - Number of feeds pending fetch
- `feed_velocity_articles_per_hour` (gauge per feed) - Current velocity
- `average_refresh_interval_seconds` (gauge per feed) - Current interval

**System Metrics:**
- `database_connection_pool_size` (gauge)
- `memory_usage_bytes` (gauge)
- `goroutines_active` (gauge) - If using Go alternative

### 5.2 Logging Strategy

**Structured Logging Format:**

```python
import structlog

logger = structlog.get_logger()

# Success log
logger.info(
    "feed_fetched",
    feed_id="reuters-world",
    articles_found=12,
    articles_new=8,
    duration_ms=1234,
    status_code=200
)

# Error log
logger.error(
    "feed_fetch_failed",
    feed_id="bloomberg-markets",
    error_type="TimeoutError",
    attempt=3,
    duration_ms=10000
)

# Performance warning
logger.warning(
    "slow_fetch_detected",
    feed_id="cnbc-breaking",
    duration_ms=8500,
    threshold_ms=5000
)
```

**Log Levels:**
- `DEBUG` - Detailed parsing information, cache hits/misses
- `INFO` - Successful operations, statistics updates
- `WARNING` - Slow operations, retry attempts
- `ERROR` - Failed fetches, parsing errors
- `CRITICAL` - System-level failures, database unavailable

### 5.3 Health Check Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """System health check endpoint"""
    checks = {
        "database": await check_database_connection(),
        "scheduler": scheduler.running,
        "feeds_active": await count_active_feeds(),
        "last_successful_fetch": await get_last_fetch_time()
    }

    healthy = all(checks.values())
    status_code = 200 if healthy else 503

    return {
        "status": "healthy" if healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }, status_code
```

---

## 6. Error Handling & Recovery

### 6.1 Error Categories

**Transient Errors (Retry):**
- Network timeouts
- HTTP 5xx errors
- Temporary DNS failures
- Rate limiting (429)

**Permanent Errors (Disable Feed):**
- HTTP 404 (feed not found)
- HTTP 410 (feed gone)
- Consecutive errors threshold exceeded (e.g., 10)
- Invalid RSS format (persistent)

**Handling Strategy:**

```python
class ErrorHandler:
    MAX_CONSECUTIVE_ERRORS = 10

    async def handle_fetch_error(self, feed_id: str, error: Exception):
        """Handle feed fetch errors with exponential backoff"""
        stats = await self.db.get_feed_stats(feed_id)
        stats.consecutive_errors += 1

        if stats.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
            # Disable feed after too many errors
            await self.db.update_feed_enabled(feed_id, enabled=False)
            await self._notify_admin(
                f"Feed {feed_id} disabled after {stats.consecutive_errors} errors"
            )
            return

        # Calculate backoff delay
        backoff_minutes = min(2 ** stats.consecutive_errors, 60)
        next_retry = datetime.utcnow() + timedelta(minutes=backoff_minutes)

        await self.db.update_feed_schedule(feed_id, next_retry)

        logger.warning(
            "feed_error_retry_scheduled",
            feed_id=feed_id,
            error_count=stats.consecutive_errors,
            next_retry=next_retry.isoformat()
        )

    async def handle_success(self, feed_id: str):
        """Reset error count on successful fetch"""
        await self.db.execute(
            "UPDATE feed_stats SET consecutive_errors = 0 WHERE feed_id = ?",
            (feed_id,)
        )
```

### 6.2 Circuit Breaker Pattern

For external services (future enhancement):

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def fetch_with_circuit_breaker(url: str):
    """Fetch with circuit breaker to prevent cascade failures"""
    return await http_client.get(url)
```

---

## 7. Database Schema Summary

```sql
-- Complete schema for ingestion system

-- Main articles table (from previous design)
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    url TEXT NOT NULL UNIQUE,
    headline TEXT NOT NULL,
    source TEXT NOT NULL,
    publish_datetime TIMESTAMP NOT NULL,
    raw_content TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_id TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE INDEX idx_articles_publish ON articles(publish_datetime DESC);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_event ON articles(event_id);

-- Feed schedules
CREATE TABLE IF NOT EXISTS feed_schedules (
    feed_id TEXT PRIMARY KEY,
    feed_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    next_fetch_time TIMESTAMP NOT NULL,
    priority_score REAL DEFAULT 1.0,
    enabled BOOLEAN DEFAULT 1,
    etag TEXT,
    last_modified TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_next_fetch ON feed_schedules(next_fetch_time, priority_score);

-- Feed statistics
CREATE TABLE IF NOT EXISTS feed_stats (
    feed_id TEXT PRIMARY KEY,
    articles_per_hour REAL DEFAULT 0.0,
    hourly_distribution TEXT DEFAULT '[]',
    last_fetch_time TIMESTAMP,
    last_successful_fetch TIMESTAMP,
    total_articles_fetched INTEGER DEFAULT 0,
    consecutive_errors INTEGER DEFAULT 0,
    avg_articles_per_fetch REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feed_schedules(feed_id)
);

-- Deduplication cache
CREATE TABLE IF NOT EXISTS dedup_cache (
    content_hash TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP GENERATED ALWAYS AS (
        datetime(created_at, '+7 days')
    ) STORED
);

CREATE INDEX idx_dedup_expires ON dedup_cache(expires_at);

-- Fetch history (for analytics)
CREATE TABLE IF NOT EXISTS fetch_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    feed_id TEXT NOT NULL,
    fetch_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_code INTEGER,
    articles_found INTEGER DEFAULT 0,
    articles_new INTEGER DEFAULT 0,
    duration_ms INTEGER,
    error_message TEXT,
    FOREIGN KEY (feed_id) REFERENCES feed_schedules(feed_id)
);

CREATE INDEX idx_fetch_history_time ON fetch_history(fetch_time DESC);
CREATE INDEX idx_fetch_history_feed ON fetch_history(feed_id);
```

---

## 8. Performance Optimization

### 8.1 SQLite Connection Pooling

```python
import aiosqlite
from typing import Optional

class DatabasePool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def initialize(self):
        """Create connection pool"""
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )

            # Enable WAL mode for better concurrency
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=10000")
            await conn.execute("PRAGMA temp_store=MEMORY")

            await self.connections.put(conn)

        self._initialized = True

    async def acquire(self) -> aiosqlite.Connection:
        """Get connection from pool"""
        return await self.connections.get()

    async def release(self, conn: aiosqlite.Connection):
        """Return connection to pool"""
        await self.connections.put(conn)

    async def close_all(self):
        """Close all connections"""
        while not self.connections.empty():
            conn = await self.connections.get()
            await conn.close()
```

### 8.2 Batch Operations

- Insert articles in batches of 100 (configurable)
- Use prepared statements for repeated queries
- Batch deduplication cache updates

### 8.3 Caching Strategy

**In-Memory Cache (LRU):**
- Deduplication cache (10,000 entries)
- Feed statistics (all active feeds)
- Recent article IDs

**Database Cache:**
- Deduplication cache (7-day retention)
- Feed history (for analytics)

---

## 9. Deployment Considerations

### 9.1 MVP Deployment (Single Instance)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose health check port
EXPOSE 8080

# Run ingestion service
CMD ["python", "-m", "ingestion.main"]
```

**Requirements.txt:**
```
aiohttp==3.9.1
aiosqlite==0.19.0
feedparser==6.0.10
apscheduler==3.10.4
pydantic==2.5.0
pydantic-settings==2.1.0
structlog==23.2.0
fastapi==0.104.1
uvicorn==0.24.0
```

### 9.2 Docker Compose

```yaml
version: '3.8'

services:
  ingestion:
    build: .
    volumes:
      - ./data:/data
      - ./config:/app/config
    environment:
      - DATABASE_PATH=/data/news_trading.db
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 9.3 Future Scaling Considerations

**When to scale (not for MVP):**
- Processing >100 feeds
- Handling >10,000 articles/hour
- Multiple consumer applications

**Scaling approach:**
- Add Redis for distributed scheduling
- Use message queue (RabbitMQ/Kafka) for events
- Horizontal scaling with leader election
- Separate fetcher and processor services

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/test_parser.py
import pytest
from ingestion.parser import RSSParser

@pytest.mark.asyncio
async def test_parse_valid_rss():
    """Test parsing of valid RSS feed"""
    sample_rss = """
    <?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Test Article</title>
                <link>https://example.com/article1</link>
                <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """

    parser = RSSParser(mock_db)
    articles = await parser.parse_feed(sample_rss, "TestSource")

    assert len(articles) == 1
    assert articles[0].headline == "Test Article"
    assert articles[0].source == "TestSource"

@pytest.mark.asyncio
async def test_deduplication():
    """Test that duplicate articles are filtered"""
    parser = RSSParser(mock_db)

    # Parse same feed twice
    articles1 = await parser.parse_feed(sample_rss, "TestSource")
    articles2 = await parser.parse_feed(sample_rss, "TestSource")

    assert len(articles1) == 1
    assert len(articles2) == 0  # Duplicates filtered
```

### 10.2 Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_ingestion_pipeline():
    """Test complete ingestion flow"""
    orchestrator = IngestionOrchestrator(test_config)

    # Add test feed
    await orchestrator.add_feed({
        'feed_id': 'test-feed',
        'feed_url': 'http://localhost:8888/test.rss',
        'source_name': 'TestSource'
    })

    # Run single fetch cycle
    await orchestrator._fetch_cycle()

    # Verify articles in database
    articles = await db.execute_all(
        "SELECT * FROM articles WHERE source = 'TestSource'"
    )

    assert len(articles) > 0
```

### 10.3 Load Testing

```python
# tests/load_test.py
import asyncio
import time

async def load_test_concurrent_fetches():
    """Test system under concurrent load"""
    feeds = [f"feed-{i}" for i in range(100)]

    start = time.time()

    tasks = [
        orchestrator._process_feed(create_mock_feed(feed_id))
        for feed_id in feeds
    ]

    await asyncio.gather(*tasks)

    duration = time.time() - start

    print(f"Processed {len(feeds)} feeds in {duration:.2f}s")
    print(f"Throughput: {len(feeds)/duration:.2f} feeds/sec")
```

---

## 11. Maintenance & Operations

### 11.1 Daily Operations

**Automated Tasks:**
- Deduplication cache cleanup (hourly)
- Feed statistics recalculation (daily)
- Error log rotation (daily)
- Database vacuum (weekly)

**Manual Checks:**
- Review disabled feeds
- Analyze slow feeds
- Check error patterns

### 11.2 Adding New Feeds

```python
async def add_feed(
    feed_url: str,
    source_name: str,
    priority: float = 1.0
):
    """Add new RSS feed to system"""
    feed_id = hashlib.md5(feed_url.encode()).hexdigest()[:16]

    await db.execute(
        """
        INSERT INTO feed_schedules (
            feed_id, feed_url, source_name,
            priority_score, next_fetch_time
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            feed_id,
            feed_url,
            source_name,
            priority,
            datetime.utcnow()  # Fetch immediately
        )
    )

    # Initialize statistics
    await db.execute(
        "INSERT INTO feed_stats (feed_id) VALUES (?)",
        (feed_id,)
    )
```

### 11.3 Monitoring Queries

```sql
-- Check feed health
SELECT
    fs.feed_id,
    fs.source_name,
    fs.enabled,
    fst.consecutive_errors,
    fst.last_successful_fetch,
    fst.articles_per_hour
FROM feed_schedules fs
JOIN feed_stats fst ON fs.feed_id = fst.feed_id
WHERE fs.enabled = 1
ORDER BY fst.consecutive_errors DESC;

-- Top performing feeds
SELECT
    source_name,
    COUNT(*) as article_count,
    AVG(JULIANDAY('now') - JULIANDAY(publish_datetime)) * 24 as avg_age_hours
FROM articles
WHERE publish_datetime > datetime('now', '-24 hours')
GROUP BY source_name
ORDER BY article_count DESC;
```

---

## 12. Migration Path

### 12.1 Initial Setup

```sql
-- Initialize feed schedules with example feeds
INSERT INTO feed_schedules (feed_id, feed_url, source_name, priority_score, next_fetch_time)
VALUES
    ('reuters-world', 'https://www.reuters.com/rssFeed/worldNews', 'Reuters', 1.0, datetime('now')),
    ('bloomberg-mkts', 'https://www.bloomberg.com/feed/markets.rss', 'Bloomberg', 1.2, datetime('now')),
    ('cnbc-breaking', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 'CNBC', 1.5, datetime('now'));

-- Initialize statistics
INSERT INTO feed_stats (feed_id, hourly_distribution)
SELECT feed_id, '[]' FROM feed_schedules;
```

### 12.2 Zero-Downtime Updates

```python
async def safe_schema_update():
    """Apply schema changes without downtime"""
    # 1. Create new table with updated schema
    await db.execute("CREATE TABLE feed_stats_new AS SELECT * FROM feed_stats")

    # 2. Add new columns
    await db.execute("ALTER TABLE feed_stats_new ADD COLUMN new_field TEXT")

    # 3. Atomic rename
    async with db.transaction():
        await db.execute("DROP TABLE feed_stats")
        await db.execute("ALTER TABLE feed_stats_new RENAME TO feed_stats")
```

---

## Appendix A: Performance Benchmarks

**Expected Performance (MVP):**
- Feed fetch throughput: 10-20 feeds/second
- Article insertion rate: 1000+ articles/second (batched)
- Deduplication check: <1ms (in-memory cache hit)
- Adaptive scheduling calculation: <5ms
- Memory footprint: <200MB (for 50 feeds)

**Bottlenecks to Monitor:**
- SQLite write lock contention (WAL mode mitigates)
- Network I/O for slow feeds
- Deduplication cache size

---

## Appendix B: Alternative Technologies

### If Node.js Preferred:

**Libraries:**
```json
{
  "dependencies": {
    "rss-parser": "^3.13.0",
    "node-cron": "^3.0.3",
    "better-sqlite3": "^9.2.0",
    "p-queue": "^7.4.1",
    "pino": "^8.17.0"
  }
}
```

**Pros:**
- Event-driven architecture (natural fit)
- Strong async/await support
- Rich npm ecosystem

**Cons:**
- Less robust RSS parsing libraries
- SQLite support not as mature as Python
- Heavier runtime footprint

---

## Conclusion

This design provides a production-ready RSS ingestion system optimized for MVP deployment with clear scaling paths. Key features:

✅ **Adaptive scheduling** - Automatically optimizes fetch intervals
✅ **Robust error handling** - Graceful degradation and recovery
✅ **High performance** - Async I/O with batching and caching
✅ **Observable** - Comprehensive metrics and logging
✅ **Maintainable** - Clear component boundaries and configuration

**Next Steps:**
1. Review and approve architecture
2. Implement core components (3-5 days)
3. Write comprehensive tests (2 days)
4. Deploy MVP to staging (1 day)
5. Monitor and iterate based on real-world performance

**Estimated MVP Development Time:** 6-8 days for experienced backend developer

---

*Document Version: 1.0*
*Last Updated: 2025-10-22*
*Author: Backend Systems Developer*
