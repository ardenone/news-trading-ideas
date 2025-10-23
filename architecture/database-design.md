# News Trading Ideas System - Database Design

## Overview

This document describes the SQLite database schema for the news trading ideas system, optimized for fast queries, efficient storage, and automated data retention.

## Design Principles

1. **Query Optimization First**: Indexes designed for the most common query patterns
2. **Minimal Storage Overhead**: Lean schema with only essential fields
3. **Automatic Maintenance**: Triggers and views reduce application complexity
4. **Fast Duplicate Detection**: Content hashing prevents reprocessing
5. **Event-Centric Architecture**: News events aggregate multiple articles

## Entity Relationship Diagram

```
┌─────────────┐
│ rss_feeds   │
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐      ┌──────────────┐
│  articles   │◄────►│ news_events  │
└─────────────┘  N:M └──────┬───────┘
                      │      │ 1:N
      event_articles  │      ▼
      (mapping table) │  ┌──────────────┐
                      │  │trading_ideas │
                      │  └──────┬───────┘
                      │         │ 1:N
                      │         ▼
                      │  ┌─────────────────┐
                      └─►│trade_strategies │
                         └─────────────────┘
```

## Core Tables

### 1. rss_feeds

Stores RSS feed sources with scheduling information.

**Key Fields:**
- `feed_url`: Unique RSS feed URL
- `update_interval`: Seconds between fetches (default: 300)
- `next_fetch_scheduled`: When to fetch next (enables efficient polling)
- `category`: Feed categorization (e.g., 'general', 'crypto', 'forex')

**Indexes:**
- `idx_feeds_next_fetch`: Find feeds ready to fetch (WHERE is_active = 1)
- `idx_feeds_category`: Category-based feed filtering

**Query Pattern:**
```sql
-- Find feeds ready to fetch
SELECT * FROM rss_feeds
WHERE is_active = 1
  AND next_fetch_scheduled <= datetime('now')
ORDER BY next_fetch_scheduled ASC;
```

### 2. articles

Stores individual news articles/headlines with processing status.

**Key Fields:**
- `headline`: Article title
- `processed_status`: Tracks processing pipeline (pending → processing → processed)
- `content_hash`: SHA-256 hash for duplicate detection
- `publish_datetime`: Article publication time (critical for ranking)

**Indexes:**
- `idx_articles_processing`: **MOST CRITICAL** - finds unprocessed articles
- `idx_articles_recent`: Time-based queries
- `idx_articles_content_hash`: Fast duplicate detection

**Query Patterns:**
```sql
-- Get next batch of articles to process
SELECT * FROM articles
WHERE processed_status = 'pending'
ORDER BY publish_datetime DESC
LIMIT 100;

-- Check for duplicate before inserting
SELECT article_id FROM articles
WHERE content_hash = ?
LIMIT 1;
```

### 3. news_events

Aggregates related articles into newsworthy events.

**Key Fields:**
- `event_summary`: Human-readable event description
- `event_key`: Normalized key for grouping (e.g., "fed_rate_hike_2024")
- `source_count`: Number of distinct sources reporting (indicates importance)
- `relevance_score`: Computed score for ranking
- `status`: active | stale | archived

**Indexes:**
- `idx_events_active_ranked`: **PRIMARY RANKING INDEX** - sorts by importance
- `idx_events_timerange`: Time-window queries
- `idx_events_key`: Event grouping

**Query Pattern:**
```sql
-- Get top events ranked by importance
SELECT * FROM v_active_events_ranked
WHERE status = 'active'
  AND hours_old < 24
ORDER BY source_count DESC, first_reported_time DESC
LIMIT 20;
```

**Ranking Algorithm:**
Events are ranked by:
1. `source_count DESC` - More sources = more important
2. `first_reported_time DESC` - More recent = more relevant

### 4. event_articles

Many-to-many mapping between events and articles.

**Key Fields:**
- `contribution_score`: How much this article contributed to the event (future use)

**Indexes:**
- `idx_event_articles_event`: Find all articles in an event
- `idx_event_articles_article`: Find which event an article belongs to

**Automatic Maintenance:**
- Trigger updates `news_events.article_count` on insert/delete
- Cascade deletes when parent event/article is deleted

### 5. trading_ideas

AI-generated trading ideas based on news events.

**Key Fields:**
- `trading_thesis`: Core reasoning for the trade
- `confidence_score`: AI confidence (0.0 - 1.0)
- `status`: new | reviewed | actioned | expired | rejected
- `expires_at`: Auto-expiration timestamp

**Indexes:**
- `idx_ideas_status`: Find new/actionable ideas
- `idx_ideas_expiration`: Cleanup expired ideas

**Query Pattern:**
```sql
-- Get fresh trading ideas
SELECT * FROM v_trading_ideas_summary
WHERE status = 'new'
  AND generated_at > datetime('now', '-4 hours')
ORDER BY confidence_score DESC;
```

### 6. trade_strategies

Concrete trading strategies derived from ideas.

**Key Fields:**
- `strategy_type`: momentum | reversal | pairs | options | futures
- `ticker`: Trading symbol
- `entry_conditions`: When to enter
- `exit_target_profit`: Profit target (%)
- `exit_target_loss`: Stop loss (%)
- `time_horizon`: intraday | swing | position | long-term

**Indexes:**
- `idx_strategies_ticker`: Find strategies by symbol
- `idx_strategies_type`: Find strategies by type

**Query Pattern:**
```sql
-- Find active strategies for a ticker
SELECT * FROM trade_strategies
WHERE ticker = 'AAPL'
  AND status IN ('pending', 'active')
ORDER BY created_at DESC;
```

## Index Strategy

### Performance Optimization

1. **Partial Indexes**: Use WHERE clauses to index only relevant rows
   - `idx_articles_processing WHERE processed_status = 'pending'`
   - Reduces index size by 80%+ in production

2. **Covering Indexes**: Include frequently queried columns
   - `idx_events_active_ranked` covers status, source_count, first_reported_time

3. **Composite Indexes**: Match query ORDER BY clauses
   - `(source_count DESC, first_reported_time DESC)` matches ranking query

### Index Maintenance

SQLite automatically maintains indexes. Run `ANALYZE` after:
- Bulk inserts (>1000 rows)
- Schema changes
- Major data deletions

```sql
ANALYZE;
```

## Sample Queries

### Key Operations

#### 1. Find Feeds Ready to Fetch
```sql
SELECT feed_id, feed_url, source_name
FROM rss_feeds
WHERE is_active = 1
  AND next_fetch_scheduled <= datetime('now')
ORDER BY next_fetch_scheduled ASC
LIMIT 10;
```

#### 2. Get Unprocessed Articles
```sql
SELECT article_id, headline, source, publish_datetime
FROM articles
WHERE processed_status = 'pending'
ORDER BY publish_datetime DESC
LIMIT 100;
```

#### 3. Rank Active Events by Importance
```sql
SELECT
    event_id,
    event_summary,
    source_count,
    article_count,
    ROUND((julianday('now') - julianday(first_reported_time)) * 24, 2) AS hours_old
FROM news_events
WHERE status = 'active'
  AND first_reported_time > datetime('now', '-24 hours')
ORDER BY source_count DESC, first_reported_time DESC
LIMIT 20;
```

#### 4. Find Trading Ideas for an Event
```sql
SELECT
    ti.idea_id,
    ti.headline,
    ti.trading_thesis,
    ti.confidence_score,
    COUNT(ts.strategy_id) AS strategy_count
FROM trading_ideas ti
LEFT JOIN trade_strategies ts ON ti.idea_id = ts.idea_id
WHERE ti.event_id = ?
  AND ti.status = 'new'
GROUP BY ti.idea_id
ORDER BY ti.confidence_score DESC;
```

#### 5. Check for Duplicate Article
```sql
SELECT article_id
FROM articles
WHERE content_hash = ?
LIMIT 1;
```

#### 6. Get Event Articles with Sources
```sql
SELECT
    a.article_id,
    a.headline,
    a.source,
    a.publish_datetime,
    a.url
FROM event_articles ea
JOIN articles a ON ea.article_id = a.article_id
WHERE ea.event_id = ?
ORDER BY a.publish_datetime DESC;
```

## Data Retention Strategy

### Automatic Cleanup

The system implements a 24-hour retention policy for processed data:

#### Cleanup Query (Run Hourly)
```sql
-- Archive old events
UPDATE news_events
SET status = 'archived'
WHERE status = 'active'
  AND last_updated < datetime('now', '-24 hours');

-- Mark stale events
UPDATE news_events
SET status = 'stale'
WHERE status = 'active'
  AND last_updated < datetime('now', '-6 hours');

-- Delete old articles (cascade deletes event_articles)
DELETE FROM articles
WHERE publish_datetime < datetime('now', '-24 hours')
  AND processed_status = 'processed';

-- Expire old trading ideas
UPDATE trading_ideas
SET status = 'expired'
WHERE status = 'new'
  AND generated_at < datetime('now', '-12 hours');

-- Update cleanup timestamp
UPDATE system_metadata
SET value = datetime('now')
WHERE key = 'last_cleanup_run';
```

#### Retention Schedule

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Unprocessed Articles | Indefinite | Need to process |
| Processed Articles | 24 hours | Historical context |
| Active Events | 6 hours | Trading relevance |
| Stale Events | 24 hours | Analysis only |
| Trading Ideas | 12 hours | Execution window |
| Trade Strategies | 30 days | Performance tracking |

### Storage Estimates

For 100 feeds fetched every 5 minutes:

- **Articles per hour**: ~1,200
- **Articles per day**: ~28,800
- **Events per day**: ~500-1,000
- **Database size (24h)**: ~50-100 MB
- **Peak memory**: <200 MB

With 24-hour retention, storage remains constant.

## Triggers & Automation

### Automatic Updates

1. **Event Article Count**: Auto-updates when articles mapped
2. **Feed Timestamps**: Auto-updates on modification
3. **Event Staleness**: Auto-marks events older than 6 hours
4. **Cascade Deletes**: Removes orphaned records automatically

### Example Trigger
```sql
CREATE TRIGGER trg_update_event_article_count_insert
AFTER INSERT ON event_articles
BEGIN
    UPDATE news_events
    SET article_count = article_count + 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE event_id = NEW.event_id;
END;
```

## Views for Simplified Access

### v_active_events_ranked
Pre-computed ranking of active events with trading idea counts.

```sql
SELECT * FROM v_active_events_ranked
WHERE hours_old < 12
LIMIT 10;
```

### v_pending_articles
All articles awaiting processing with metadata.

```sql
SELECT * FROM v_pending_articles
ORDER BY publish_datetime DESC;
```

### v_trading_ideas_summary
Trading ideas with event context and strategy counts.

```sql
SELECT * FROM v_trading_ideas_summary
WHERE status = 'new'
ORDER BY confidence_score DESC;
```

## Migration & Versioning

Schema version tracked in `system_metadata` table:
```sql
SELECT value FROM system_metadata WHERE key = 'schema_version';
-- Returns: '1.0.0'
```

For future migrations:
1. Create migration script: `migrations/v1.0.0_to_v1.1.0.sql`
2. Update schema_version in system_metadata
3. Document changes in this file

## Performance Tuning

### SQLite Configuration

Recommended PRAGMA settings for production:

```sql
-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode = WAL;

-- Increase cache size (10MB)
PRAGMA cache_size = -10000;

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Synchronous = NORMAL for better write performance
PRAGMA synchronous = NORMAL;

-- Auto-vacuum to reclaim space
PRAGMA auto_vacuum = INCREMENTAL;
```

### Query Optimization Tips

1. **Use Views**: Pre-computed joins reduce query complexity
2. **Batch Inserts**: Use transactions for bulk operations
3. **Prepared Statements**: Reuse query plans
4. **EXPLAIN QUERY PLAN**: Verify index usage

```sql
EXPLAIN QUERY PLAN
SELECT * FROM articles
WHERE processed_status = 'pending'
ORDER BY publish_datetime DESC;
```

Expected output should show `USING INDEX idx_articles_processing`.

## Backup & Recovery

### Backup Strategy
```bash
# Daily backup
sqlite3 news_trading.db ".backup '/backups/news_trading_$(date +%Y%m%d).db'"

# Export to SQL
sqlite3 news_trading.db .dump > backup.sql
```

### Recovery
```bash
# Restore from backup
sqlite3 news_trading.db < backup.sql
```

## Security Considerations

1. **No Sensitive Data**: Schema designed for public news only
2. **Input Validation**: Use parameterized queries (prevent SQL injection)
3. **File Permissions**: Restrict database file to application user
4. **Connection Limits**: Single writer, multiple readers (WAL mode)

## Testing Recommendations

### Unit Tests
- Test duplicate detection (content_hash)
- Verify trigger execution (article_count)
- Validate cascading deletes
- Test index coverage (EXPLAIN QUERY PLAN)

### Integration Tests
- Full pipeline: RSS fetch → article → event → idea → strategy
- Concurrent writes (WAL mode)
- Retention cleanup (24-hour cycle)
- Query performance (<100ms for ranked events)

### Load Tests
- 1,000 articles/minute insertion
- 100 concurrent readers
- Event ranking with 10,000 active events

## Future Enhancements

Potential schema additions:

1. **Sentiment Scores**: Add sentiment analysis results to articles
2. **User Feedback**: Track which ideas led to profitable trades
3. **Price Data**: Link strategies to actual price movements
4. **Backtesting**: Store historical performance metrics
5. **Alert Rules**: User-defined triggers for notifications

---

**Schema Version**: 1.0.0
**Last Updated**: 2025-10-22
**Maintained By**: Database Architect Agent
