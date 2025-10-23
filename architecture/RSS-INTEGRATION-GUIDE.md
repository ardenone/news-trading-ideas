# RSS INTEGRATION GUIDE - Trading System Implementation
**Last Updated:** October 22, 2025
**Purpose:** Technical guide for implementing RSS feed ingestion

---

## 📋 TABLE OF CONTENTS

1. [Architecture Overview](#architecture-overview)
2. [Polling Strategy](#polling-strategy)
3. [Error Handling](#error-handling)
4. [Deduplication](#deduplication)
5. [Workarounds for Blocked Feeds](#workarounds-for-blocked-feeds)
6. [Rate Limiting](#rate-limiting)
7. [Storage & Indexing](#storage--indexing)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Code Examples](#code-examples)
10. [Testing Strategy](#testing-strategy)

---

## 🏗️ ARCHITECTURE OVERVIEW

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FEED ORCHESTRATOR                        │
│  (Manages polling schedule, priorities, and failover)       │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬────────────────┬──────────────┐
    ▼            ▼            ▼                ▼              ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────────────┐  ┌────────┐
│ Fetcher│  │ Fetcher│  │ Fetcher│  │ Fetcher (Proxy)│  │ Fetcher│
│  Pool  │  │  Pool  │  │  Pool  │  │   (Bloomberg)  │  │  Pool  │
└────┬───┘  └────┬───┘  └────┬───┘  └────────┬───────┘  └────┬───┘
     │           │           │               │               │
     └───────────┼───────────┼───────────────┼───────────────┘
                 │           │               │
                 ▼           ▼               ▼
         ┌────────────────────────────────────────┐
         │        XML/RSS PARSER                  │
         │  (Handles RSS 2.0, Atom, malformed)    │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │      DEDUPLICATION ENGINE              │
         │  (Hash-based, fuzzy matching, GUID)    │
         └────────────┬───────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐
    │Article │  │ Content  │  │  Search  │
    │Database│  │  Cache   │  │  Index   │
    │(Postgres)│ │ (Redis)  │  │(Elastic) │
    └────────┘  └──────────┘  └──────────┘
```

### Technology Stack Recommendations

**Feed Fetching:**
- **Node.js:** `feedparser`, `axios`, `cheerio` (for HTML parsing)
- **Python:** `feedparser`, `requests`, `BeautifulSoup`
- **Go:** `mmcdole/gofeed`, `net/http`

**Storage:**
- **Primary Database:** PostgreSQL (article metadata, relationships)
- **Cache:** Redis (recent articles, deduplication cache)
- **Search:** Elasticsearch (full-text search, filtering)

**Queue System:**
- **RabbitMQ** or **Redis Queue** for async processing
- **Kafka** for high-throughput streaming (if scaling)

**Monitoring:**
- **Prometheus** + **Grafana** (metrics)
- **Sentry** (error tracking)
- **PagerDuty** (alerts)

---

## ⏰ POLLING STRATEGY

### Frequency Tiers

```javascript
const POLLING_SCHEDULE = {
  "real-time": {
    interval: 5 * 60 * 1000, // 5 minutes
    feeds: [
      "cnbc-markets",
      "yahoo-finance",
      "benzinga",
      "techcrunch",
      "nbc-news",
      "cbs-news"
    ]
  },
  "hourly": {
    interval: 30 * 60 * 1000, // 30 minutes
    feeds: [
      "wsj-markets",
      "ft-home",
      "bbc-business",
      "the-hill-news",
      "washington-post-politics"
    ]
  },
  "daily": {
    interval: 2 * 60 * 60 * 1000, // 2 hours
    feeds: [
      "barrons-markets",
      "npr-politics",
      "propublica"
    ]
  }
};
```

### Adaptive Polling

```javascript
class AdaptiveFeedScheduler {
  constructor() {
    this.baseIntervals = POLLING_SCHEDULE;
    this.feedStats = new Map();
  }

  // Adjust polling based on feed behavior
  adjustInterval(feedId, articlesFound) {
    const stats = this.feedStats.get(feedId) || {
      avgArticles: 0,
      samples: 0,
      consecutiveEmpty: 0
    };

    stats.avgArticles = (stats.avgArticles * stats.samples + articlesFound)
                        / (stats.samples + 1);
    stats.samples++;

    if (articlesFound === 0) {
      stats.consecutiveEmpty++;
    } else {
      stats.consecutiveEmpty = 0;
    }

    // Slow down if consistently empty
    if (stats.consecutiveEmpty >= 5) {
      return this.baseIntervals[feedId] * 2;
    }

    // Speed up if high volume
    if (stats.avgArticles > 10) {
      return Math.max(
        this.baseIntervals[feedId] * 0.75,
        3 * 60 * 1000 // Min 3 minutes
      );
    }

    return this.baseIntervals[feedId];
  }
}
```

### Distributed Polling (for scale)

```javascript
// Use consistent hashing to distribute feeds across workers
const WORKER_COUNT = 4;

function assignFeedToWorker(feedId, workerCount) {
  const hash = hashCode(feedId);
  return hash % workerCount;
}

// Worker only polls feeds assigned to it
class FeedWorker {
  constructor(workerId, totalWorkers) {
    this.workerId = workerId;
    this.totalWorkers = totalWorkers;
  }

  shouldPollFeed(feedId) {
    return assignFeedToWorker(feedId, this.totalWorkers) === this.workerId;
  }
}
```

---

## 🛡️ ERROR HANDLING

### Error Classification

```javascript
const ERROR_TYPES = {
  NETWORK: {
    TIMEOUT: { code: 'NET_TIMEOUT', retry: true, delay: 5000 },
    DNS_FAIL: { code: 'NET_DNS', retry: true, delay: 30000 },
    CONNECTION_REFUSED: { code: 'NET_REFUSED', retry: true, delay: 60000 }
  },
  HTTP: {
    400: { code: 'HTTP_BAD_REQUEST', retry: false, action: 'log_and_alert' },
    403: { code: 'HTTP_FORBIDDEN', retry: false, action: 'check_robots_txt' },
    404: { code: 'HTTP_NOT_FOUND', retry: false, action: 'disable_feed' },
    429: { code: 'HTTP_RATE_LIMIT', retry: true, delay: 300000 }, // 5 min
    500: { code: 'HTTP_SERVER_ERROR', retry: true, delay: 60000 },
    503: { code: 'HTTP_UNAVAILABLE', retry: true, delay: 120000 }
  },
  PARSE: {
    INVALID_XML: { code: 'PARSE_XML', retry: false, action: 'log_sample' },
    MALFORMED_DATE: { code: 'PARSE_DATE', retry: false, action: 'skip_item' },
    MISSING_REQUIRED: { code: 'PARSE_REQUIRED', retry: false, action: 'skip_item' }
  },
  BUSINESS: {
    NO_NEW_ITEMS: { code: 'BIZ_NO_ITEMS', retry: false, action: 'continue' },
    ALL_DUPLICATES: { code: 'BIZ_ALL_DUPS', retry: false, action: 'continue' },
    STALE_FEED: { code: 'BIZ_STALE', retry: false, action: 'alert_if_24h' }
  }
};
```

### Retry Logic with Exponential Backoff

```javascript
class FeedFetcher {
  async fetchWithRetry(feedUrl, maxRetries = 3) {
    let attempt = 0;
    let lastError;

    while (attempt < maxRetries) {
      try {
        const response = await axios.get(feedUrl, {
          timeout: 10000,
          headers: {
            'User-Agent': 'NewsTrading/1.0 (compatible; trading system)',
            'Accept': 'application/rss+xml, application/xml, text/xml'
          }
        });

        return response.data;

      } catch (error) {
        lastError = error;
        attempt++;

        const errorInfo = this.classifyError(error);

        if (!errorInfo.retry || attempt >= maxRetries) {
          throw error;
        }

        const delay = this.calculateBackoff(attempt, errorInfo.delay);
        console.log(`Retry ${attempt}/${maxRetries} after ${delay}ms`);
        await this.sleep(delay);
      }
    }

    throw lastError;
  }

  calculateBackoff(attempt, baseDelay = 5000) {
    // Exponential backoff with jitter
    const exponential = baseDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 1000;
    return Math.min(exponential + jitter, 60000); // Max 1 minute
  }

  classifyError(error) {
    if (error.code === 'ECONNABORTED') {
      return ERROR_TYPES.NETWORK.TIMEOUT;
    }
    if (error.code === 'ENOTFOUND') {
      return ERROR_TYPES.NETWORK.DNS_FAIL;
    }
    if (error.response) {
      return ERROR_TYPES.HTTP[error.response.status] ||
             { retry: false, action: 'log_and_alert' };
    }
    return { retry: true, delay: 10000 };
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### Circuit Breaker Pattern

```javascript
class CircuitBreaker {
  constructor(feedId, threshold = 5, timeout = 60000) {
    this.feedId = feedId;
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = null;
  }

  async execute(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error(`Circuit breaker OPEN for ${this.feedId}`);
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
      console.error(`Circuit breaker OPEN for ${this.feedId}`);
    }
  }
}
```

---

## 🔄 DEDUPLICATION

### Multi-Level Deduplication Strategy

```javascript
class ArticleDeduplicator {
  constructor(redisClient, postgresClient) {
    this.redis = redisClient;
    this.db = postgresClient;
  }

  async isDuplicate(article) {
    // Level 1: Exact GUID/Link match (fastest)
    const guidKey = `article:guid:${article.guid || article.link}`;
    const existsInCache = await this.redis.exists(guidKey);
    if (existsInCache) {
      return { duplicate: true, reason: 'guid_match', level: 1 };
    }

    // Level 2: Content hash (fast, handles reprints)
    const contentHash = this.hashContent(article);
    const hashKey = `article:hash:${contentHash}`;
    const existsHash = await this.redis.exists(hashKey);
    if (existsHash) {
      return { duplicate: true, reason: 'content_hash', level: 2 };
    }

    // Level 3: Fuzzy title match (slower, catches similar stories)
    const titleSimilarity = await this.findSimilarTitle(article.title);
    if (titleSimilarity && titleSimilarity.score > 0.85) {
      return {
        duplicate: true,
        reason: 'fuzzy_title',
        level: 3,
        match: titleSimilarity
      };
    }

    // Level 4: Database check (slowest, for edge cases)
    const dbExists = await this.db.query(
      'SELECT id FROM articles WHERE link = $1 OR guid = $2 LIMIT 1',
      [article.link, article.guid]
    );
    if (dbExists.rows.length > 0) {
      return { duplicate: true, reason: 'db_match', level: 4 };
    }

    // Not a duplicate - cache it
    await this.cacheArticle(article, contentHash);
    return { duplicate: false };
  }

  hashContent(article) {
    const crypto = require('crypto');
    const content = [
      article.title || '',
      article.description?.substring(0, 200) || '',
      article.pubDate || ''
    ].join('|').toLowerCase();

    return crypto.createHash('md5').update(content).digest('hex');
  }

  async findSimilarTitle(title) {
    // Use Levenshtein distance or cosine similarity
    const recentTitles = await this.redis.zrange(
      'article:titles:recent',
      0,
      100
    );

    let bestMatch = null;
    let bestScore = 0;

    for (const storedTitle of recentTitles) {
      const score = this.similarityScore(title, storedTitle);
      if (score > bestScore) {
        bestScore = score;
        bestMatch = storedTitle;
      }
    }

    return bestScore > 0.85 ? { title: bestMatch, score: bestScore } : null;
  }

  similarityScore(str1, str2) {
    // Simple Jaccard similarity on words
    const words1 = new Set(str1.toLowerCase().split(/\s+/));
    const words2 = new Set(str2.toLowerCase().split(/\s+/));

    const intersection = new Set(
      [...words1].filter(x => words2.has(x))
    );
    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
  }

  async cacheArticle(article, contentHash) {
    const TTL = 7 * 24 * 60 * 60; // 7 days

    // Cache GUID
    await this.redis.setex(
      `article:guid:${article.guid || article.link}`,
      TTL,
      '1'
    );

    // Cache content hash
    await this.redis.setex(
      `article:hash:${contentHash}`,
      TTL,
      article.link
    );

    // Cache title for fuzzy matching
    await this.redis.zadd(
      'article:titles:recent',
      Date.now(),
      article.title
    );

    // Trim old titles (keep last 1000)
    await this.redis.zremrangebyrank('article:titles:recent', 0, -1001);
  }
}
```

### Deduplication Stats Tracking

```javascript
class DeduplicationStats {
  constructor() {
    this.stats = {
      total_checked: 0,
      duplicates_found: 0,
      by_level: { 1: 0, 2: 0, 3: 0, 4: 0 },
      by_reason: {}
    };
  }

  record(result) {
    this.stats.total_checked++;

    if (result.duplicate) {
      this.stats.duplicates_found++;
      this.stats.by_level[result.level]++;
      this.stats.by_reason[result.reason] =
        (this.stats.by_reason[result.reason] || 0) + 1;
    }
  }

  getRate() {
    return this.stats.duplicates_found / this.stats.total_checked;
  }

  report() {
    console.log('Deduplication Report:');
    console.log(`Total Checked: ${this.stats.total_checked}`);
    console.log(`Duplicates: ${this.stats.duplicates_found} (${(this.getRate() * 100).toFixed(1)}%)`);
    console.log('By Level:', this.stats.by_level);
    console.log('By Reason:', this.stats.by_reason);
  }
}
```

---

## 🔧 WORKAROUNDS FOR BLOCKED FEEDS

### Bloomberg (via OpenRSS)

```javascript
async function fetchBloombergViaOpenRSS(section = 'markets') {
  const url = `https://openrss.org/bloomberg.com/${section}`;

  try {
    const response = await axios.get(url, {
      timeout: 15000, // OpenRSS may be slower
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NewsTrading/1.0)',
        'Accept': 'application/rss+xml'
      }
    });

    return parseFeed(response.data);

  } catch (error) {
    console.error(`OpenRSS Bloomberg fetch failed: ${error.message}`);
    // Fallback: try direct Bloomberg scraping (last resort)
    return await scrapeBBloombergDirect(section);
  }
}
```

### Reuters (via Google News)

```javascript
async function fetchReutersViaGoogleNews() {
  const query = 'when:24h+allinurl:reuters.com';
  const url = `https://news.google.com/rss/search?q=${query}&ceid=US:en&hl=en-US&gl=US`;

  const response = await axios.get(url, {
    timeout: 10000,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
  });

  const feed = parseFeed(response.data);

  // Filter to only Reuters articles
  feed.items = feed.items.filter(item =>
    item.link && item.link.includes('reuters.com')
  );

  return feed;
}
```

### Business Insider (via ?service=rss)

```javascript
async function fetchBusinessInsider(section = '') {
  const baseUrl = 'https://www.businessinsider.com';
  const url = section
    ? `${baseUrl}/${section}?service=rss`
    : `${baseUrl}/?service=rss`;

  const response = await axios.get(url, {
    timeout: 10000,
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)',
      'Accept': 'application/rss+xml, application/xml'
    }
  });

  return parseFeed(response.data);
}
```

### Politico (with User-Agent Rotation)

```javascript
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
];

async function fetchPoliticoWithRotation(feedUrl) {
  const userAgent = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];

  const response = await axios.get(feedUrl, {
    timeout: 10000,
    headers: {
      'User-Agent': userAgent,
      'Accept': 'application/rss+xml',
      'Accept-Language': 'en-US,en;q=0.9',
      'Referer': 'https://www.politico.com/'
    }
  });

  return parseFeed(response.data);
}
```

---

## ⏱️ RATE LIMITING

### Token Bucket Implementation

```javascript
class RateLimiter {
  constructor(maxTokens, refillRate) {
    this.maxTokens = maxTokens; // Max requests in bucket
    this.tokens = maxTokens; // Current tokens
    this.refillRate = refillRate; // Tokens per second
    this.lastRefill = Date.now();
  }

  async acquire() {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }

    // Wait for next token
    const waitTime = (1 / this.refillRate) * 1000;
    await this.sleep(waitTime);
    return this.acquire();
  }

  refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.refillRate;

    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage
const limiter = new RateLimiter(10, 0.5); // 10 requests max, 0.5 per second

async function fetchWithRateLimit(url) {
  await limiter.acquire();
  return axios.get(url);
}
```

### Per-Source Rate Limits

```javascript
const RATE_LIMITS = {
  'cnbc.com': { maxRequests: 60, perMinutes: 1 }, // 60/min
  'wsj.com': { maxRequests: 30, perMinutes: 1 }, // 30/min
  'bloomberg.com': { maxRequests: 10, perMinutes: 1 }, // 10/min (via OpenRSS)
  'default': { maxRequests: 20, perMinutes: 1 } // 20/min default
};

class SourceRateLimiter {
  constructor() {
    this.limiters = new Map();
  }

  getLimiter(source) {
    if (!this.limiters.has(source)) {
      const config = RATE_LIMITS[source] || RATE_LIMITS.default;
      const tokensPerSecond = config.maxRequests / (config.perMinutes * 60);

      this.limiters.set(source,
        new RateLimiter(config.maxRequests, tokensPerSecond)
      );
    }
    return this.limiters.get(source);
  }

  async fetchWithLimit(url, source) {
    const limiter = this.getLimiter(source);
    await limiter.acquire();
    return axios.get(url);
  }
}
```

---

## 💾 STORAGE & INDEXING

### Database Schema (PostgreSQL)

```sql
-- Articles table
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  guid VARCHAR(500) UNIQUE NOT NULL,
  link VARCHAR(1000) NOT NULL,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  content TEXT,
  pub_date TIMESTAMP NOT NULL,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  author VARCHAR(200),
  categories VARCHAR(100)[],
  sentiment_score FLOAT,
  market_relevant BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_articles_pub_date ON articles(pub_date DESC);
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_articles_market_relevant ON articles(market_relevant)
  WHERE market_relevant = TRUE;
CREATE INDEX idx_articles_created ON articles(created_at DESC);
CREATE INDEX idx_articles_title_trgm ON articles USING gin(title gin_trgm_ops);

-- Full-text search
CREATE INDEX idx_articles_fts ON articles
  USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Sources table
CREATE TABLE sources (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  feed_url VARCHAR(500) UNIQUE NOT NULL,
  category VARCHAR(50) NOT NULL,
  update_frequency VARCHAR(20) NOT NULL,
  reliability_score FLOAT DEFAULT 1.0,
  last_fetch TIMESTAMP,
  last_success TIMESTAMP,
  consecutive_failures INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Feed stats table
CREATE TABLE feed_stats (
  id SERIAL PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  fetch_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  status VARCHAR(20) NOT NULL, -- success, failed, timeout, etc.
  articles_found INTEGER,
  new_articles INTEGER,
  duplicate_articles INTEGER,
  fetch_time_ms INTEGER,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feed_stats_source ON feed_stats(source_id);
CREATE INDEX idx_feed_stats_timestamp ON feed_stats(fetch_timestamp DESC);
```

### Elasticsearch Index Mapping

```javascript
const ARTICLE_INDEX_MAPPING = {
  settings: {
    number_of_shards: 3,
    number_of_replicas: 1,
    analysis: {
      analyzer: {
        article_analyzer: {
          type: 'custom',
          tokenizer: 'standard',
          filter: ['lowercase', 'stop', 'snowball']
        }
      }
    }
  },
  mappings: {
    properties: {
      id: { type: 'long' },
      guid: { type: 'keyword' },
      link: { type: 'keyword' },
      title: {
        type: 'text',
        analyzer: 'article_analyzer',
        fields: {
          keyword: { type: 'keyword' }
        }
      },
      description: {
        type: 'text',
        analyzer: 'article_analyzer'
      },
      content: {
        type: 'text',
        analyzer: 'article_analyzer'
      },
      pub_date: { type: 'date' },
      source: { type: 'keyword' },
      categories: { type: 'keyword' },
      sentiment_score: { type: 'float' },
      market_relevant: { type: 'boolean' },
      created_at: { type: 'date' }
    }
  }
};
```

---

## 📊 MONITORING & ALERTS

### Key Metrics to Track

```javascript
const METRICS = {
  feed_health: {
    active_feeds: 'gauge',
    stale_feeds: 'gauge', // Not updated in >24h
    failed_feeds: 'gauge',
    average_fetch_time: 'histogram'
  },
  article_processing: {
    articles_fetched: 'counter',
    articles_stored: 'counter',
    duplicates_found: 'counter',
    parse_errors: 'counter'
  },
  performance: {
    fetch_latency: 'histogram',
    parse_latency: 'histogram',
    dedup_latency: 'histogram',
    end_to_end_latency: 'histogram'
  },
  errors: {
    network_errors: 'counter',
    http_errors_by_code: 'counter',
    parse_errors: 'counter',
    timeout_errors: 'counter'
  }
};
```

### Alert Rules

```yaml
alerts:
  - name: FeedDown
    condition: feed_stats.consecutive_failures >= 3
    severity: warning
    channels: [email, slack]
    message: "Feed {{source_name}} has failed {{consecutive_failures}} times"

  - name: CriticalFeedDown
    condition: |
      feed_stats.consecutive_failures >= 5
      AND sources.category IN ('markets', 'breaking')
    severity: critical
    channels: [email, slack, pagerduty]
    message: "CRITICAL: {{source_name}} ({{category}}) down for 5+ attempts"

  - name: StaleFeed
    condition: |
      (NOW() - sources.last_success) > INTERVAL '24 hours'
      AND sources.update_frequency IN ('real-time', 'hourly')
    severity: warning
    channels: [email, slack]
    message: "Feed {{source_name}} has not updated in 24+ hours"

  - name: HighDuplicateRate
    condition: |
      (duplicates_found / articles_fetched) > 0.8
      OVER LAST 1 HOUR
    severity: info
    channels: [slack]
    message: "High duplicate rate: {{duplicate_rate}}% (feed: {{source_name}})"

  - name: HighErrorRate
    condition: |
      (SUM(errors) / SUM(requests)) > 0.1
      OVER LAST 15 MINUTES
    severity: critical
    channels: [email, slack, pagerduty]
    message: "Error rate above 10%: {{error_rate}}%"

  - name: SlowFetchTime
    condition: |
      PERCENTILE(fetch_latency, 95) > 30000
      OVER LAST 5 MINUTES
    severity: warning
    channels: [slack]
    message: "P95 fetch latency: {{p95_latency}}ms (>30s)"
```

---

## 💻 CODE EXAMPLES

### Complete Feed Processor (Node.js)

```javascript
const FeedParser = require('feedparser');
const axios = require('axios');
const { Pool } = require('pg');
const Redis = require('ioredis');

class FeedProcessor {
  constructor(config) {
    this.config = config;
    this.db = new Pool(config.postgres);
    this.redis = new Redis(config.redis);
    this.deduplicator = new ArticleDeduplicator(this.redis, this.db);
  }

  async processFeed(feedUrl, sourceId) {
    const startTime = Date.now();
    let stats = {
      articles_found: 0,
      new_articles: 0,
      duplicates: 0,
      errors: 0
    };

    try {
      // Fetch RSS feed
      const response = await axios.get(feedUrl, {
        timeout: 10000,
        responseType: 'stream',
        headers: {
          'User-Agent': 'NewsTrading/1.0'
        }
      });

      // Parse feed
      const feedparser = new FeedParser();
      const articles = [];

      response.data.pipe(feedparser);

      feedparser.on('readable', function() {
        let item;
        while (item = this.read()) {
          articles.push(item);
        }
      });

      await new Promise((resolve, reject) => {
        feedparser.on('end', resolve);
        feedparser.on('error', reject);
      });

      stats.articles_found = articles.length;

      // Process each article
      for (const article of articles) {
        try {
          const dedupResult = await this.deduplicator.isDuplicate(article);

          if (dedupResult.duplicate) {
            stats.duplicates++;
            continue;
          }

          await this.storeArticle(article, sourceId);
          stats.new_articles++;

        } catch (error) {
          console.error(`Error processing article: ${error.message}`);
          stats.errors++;
        }
      }

      // Update source stats
      await this.updateSourceStats(sourceId, 'success', stats);

      return {
        success: true,
        duration: Date.now() - startTime,
        stats
      };

    } catch (error) {
      console.error(`Feed processing failed: ${error.message}`);
      await this.updateSourceStats(sourceId, 'failed', stats, error.message);

      return {
        success: false,
        duration: Date.now() - startTime,
        error: error.message,
        stats
      };
    }
  }

  async storeArticle(article, sourceId) {
    const query = `
      INSERT INTO articles (
        guid, link, title, description, content,
        pub_date, source_id, author, categories
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      ON CONFLICT (guid) DO NOTHING
      RETURNING id
    `;

    const values = [
      article.guid || article.link,
      article.link,
      article.title,
      article.description,
      article['content:encoded'] || article.description,
      new Date(article.pubdate || article.date),
      sourceId,
      article.author,
      article.categories || []
    ];

    const result = await this.db.query(query, values);
    return result.rows[0]?.id;
  }

  async updateSourceStats(sourceId, status, stats, errorMessage = null) {
    const query = `
      INSERT INTO feed_stats (
        source_id, status, articles_found, new_articles,
        duplicate_articles, error_message
      ) VALUES ($1, $2, $3, $4, $5, $6)
    `;

    await this.db.query(query, [
      sourceId,
      status,
      stats.articles_found,
      stats.new_articles,
      stats.duplicates,
      errorMessage
    ]);

    // Update source last_fetch
    const updateSource = `
      UPDATE sources
      SET last_fetch = NOW(),
          last_success = CASE WHEN $2 = 'success' THEN NOW() ELSE last_success END,
          consecutive_failures = CASE WHEN $2 = 'success' THEN 0 ELSE consecutive_failures + 1 END
      WHERE id = $1
    `;

    await this.db.query(updateSource, [sourceId, status]);
  }
}

// Usage
const processor = new FeedProcessor({
  postgres: {
    host: 'localhost',
    database: 'trading_news',
    user: 'postgres',
    password: 'password'
  },
  redis: {
    host: 'localhost',
    port: 6379
  }
});

// Process all active feeds
async function processAllFeeds() {
  const sources = await processor.db.query(
    'SELECT id, feed_url FROM sources WHERE is_active = TRUE'
  );

  for (const source of sources.rows) {
    const result = await processor.processFeed(source.feed_url, source.id);
    console.log(`Processed ${source.feed_url}:`, result.stats);
  }
}

// Run every 5 minutes
setInterval(processAllFeeds, 5 * 60 * 1000);
```

---

## 🧪 TESTING STRATEGY

### Unit Tests

```javascript
describe('FeedProcessor', () => {
  let processor;

  beforeEach(() => {
    processor = new FeedProcessor(testConfig);
  });

  test('should parse valid RSS 2.0 feed', async () => {
    const mockFeed = `
      <?xml version="1.0"?>
      <rss version="2.0">
        <channel>
          <item>
            <title>Test Article</title>
            <link>https://example.com/article-1</link>
            <pubDate>Mon, 22 Oct 2025 10:00:00 GMT</pubDate>
          </item>
        </channel>
      </rss>
    `;

    // Mock axios response
    axios.get = jest.fn().mockResolvedValue({ data: mockFeed });

    const result = await processor.processFeed('http://example.com/rss', 1);

    expect(result.success).toBe(true);
    expect(result.stats.articles_found).toBe(1);
  });

  test('should detect duplicates by GUID', async () => {
    const article = {
      guid: 'existing-guid',
      title: 'Test Article',
      link: 'https://example.com/1'
    };

    // Pre-cache article
    await processor.redis.setex('article:guid:existing-guid', 3600, '1');

    const result = await processor.deduplicator.isDuplicate(article);

    expect(result.duplicate).toBe(true);
    expect(result.reason).toBe('guid_match');
  });

  test('should handle network timeout gracefully', async () => {
    axios.get = jest.fn().mockRejectedValue(
      new Error('ECONNABORTED')
    );

    const result = await processor.processFeed('http://example.com/rss', 1);

    expect(result.success).toBe(false);
    expect(result.error).toContain('ECONNABORTED');
  });
});
```

### Integration Tests

```javascript
describe('End-to-End Feed Processing', () => {
  test('should fetch, deduplicate, and store articles', async () => {
    // Use real feeds (but mock in CI)
    const feedUrl = 'https://feeds.bbci.co.uk/news/business/rss.xml';

    const processor = new FeedProcessor(config);
    const result = await processor.processFeed(feedUrl, 1);

    expect(result.success).toBe(true);
    expect(result.stats.articles_found).toBeGreaterThan(0);

    // Verify articles in database
    const articles = await processor.db.query(
      'SELECT COUNT(*) FROM articles WHERE source_id = 1'
    );

    expect(parseInt(articles.rows[0].count)).toBeGreaterThan(0);
  });
});
```

### Load Testing

```javascript
// Use k6 or Artillery for load testing
const loadTest = {
  target: 'http://localhost:3000/api/feeds/process',
  phases: [
    { duration: '1m', target: 10 }, // Ramp to 10 concurrent
    { duration: '5m', target: 50 }, // Sustain 50 concurrent
    { duration: '1m', target: 0 }   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<5000'], // 95% under 5s
    'http_req_failed': ['rate<0.1']      // <10% error rate
  }
};
```

---

## ✅ IMPLEMENTATION CHECKLIST

### Pre-Launch:
- [ ] Set up PostgreSQL database with schema
- [ ] Set up Redis cache
- [ ] Set up Elasticsearch index (optional)
- [ ] Implement feed fetcher with retry logic
- [ ] Implement RSS parser (support RSS 2.0 + Atom)
- [ ] Implement deduplication logic
- [ ] Set up error handling and logging
- [ ] Configure rate limiting
- [ ] Implement monitoring and alerts
- [ ] Write unit tests (>80% coverage)
- [ ] Write integration tests
- [ ] Load test with 100 concurrent feeds

### Post-Launch:
- [ ] Monitor feed health dashboard
- [ ] Review error logs daily
- [ ] Tune deduplication thresholds
- [ ] Optimize database queries
- [ ] Add Elasticsearch if needed
- [ ] Implement sentiment analysis
- [ ] Add market relevance filtering

---

**Document Version:** 1.0
**Last Updated:** October 22, 2025
**Next Review:** Post-MVP launch
**Maintainer:** Engineering Team
