-- News Trading Ideas System - SQLite Database Schema
-- Optimized for fast queries with proper indexing and data retention

-- ============================================================================
-- RSS FEEDS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rss_feeds (
    feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_url TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    update_interval INTEGER DEFAULT 300, -- seconds between updates
    last_fetched DATETIME,
    next_fetch_scheduled DATETIME,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for finding feeds ready to be fetched
CREATE INDEX idx_feeds_next_fetch
ON rss_feeds(next_fetch_scheduled, is_active)
WHERE is_active = 1;

-- Index for finding feeds by category
CREATE INDEX idx_feeds_category
ON rss_feeds(category, is_active);

-- ============================================================================
-- ARTICLES/HEADLINES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS articles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    headline TEXT NOT NULL,
    url TEXT UNIQUE,
    source TEXT NOT NULL,
    publish_datetime DATETIME NOT NULL,
    processed_status TEXT DEFAULT 'pending' CHECK(processed_status IN ('pending', 'processing', 'processed', 'failed', 'duplicate')),
    content_hash TEXT, -- for duplicate detection
    raw_content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,

    FOREIGN KEY (feed_id) REFERENCES rss_feeds(feed_id) ON DELETE CASCADE
);

-- Index for finding unprocessed articles (most critical query)
CREATE INDEX idx_articles_processing
ON articles(processed_status, publish_datetime DESC)
WHERE processed_status = 'pending';

-- Index for finding recent articles by publish time
CREATE INDEX idx_articles_recent
ON articles(publish_datetime DESC, processed_status);

-- Index for duplicate detection
CREATE INDEX idx_articles_content_hash
ON articles(content_hash)
WHERE content_hash IS NOT NULL;

-- Index for feed-based queries
CREATE INDEX idx_articles_feed
ON articles(feed_id, publish_datetime DESC);

-- ============================================================================
-- NEWS EVENTS TABLE (Grouped Headlines)
-- ============================================================================
CREATE TABLE IF NOT EXISTS news_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_summary TEXT NOT NULL,
    event_key TEXT, -- normalized key for grouping similar events
    first_reported_time DATETIME NOT NULL,
    last_updated DATETIME NOT NULL,
    source_count INTEGER DEFAULT 1,
    article_count INTEGER DEFAULT 0,
    relevance_score REAL DEFAULT 0.0, -- computed score for ranking
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'stale', 'archived')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Composite index for ranking events (primary use case)
    -- Higher source_count and more recent = more important
    CONSTRAINT idx_events_ranking UNIQUE (source_count DESC, first_reported_time DESC)
);

-- Index for finding active events sorted by importance
CREATE INDEX idx_events_active_ranked
ON news_events(status, source_count DESC, first_reported_time DESC)
WHERE status = 'active';

-- Index for finding events by time window
CREATE INDEX idx_events_timerange
ON news_events(first_reported_time DESC, status);

-- Index for grouping by event key
CREATE INDEX idx_events_key
ON news_events(event_key, status);

-- ============================================================================
-- EVENT-ARTICLE MAPPING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_articles (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    contribution_score REAL DEFAULT 1.0, -- how much this article contributed to the event
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES news_events(event_id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(article_id) ON DELETE CASCADE,

    UNIQUE(event_id, article_id)
);

-- Index for finding all articles in an event
CREATE INDEX idx_event_articles_event
ON event_articles(event_id, added_at DESC);

-- Index for finding which event an article belongs to
CREATE INDEX idx_event_articles_article
ON event_articles(article_id);

-- ============================================================================
-- TRADING IDEAS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_ideas (
    idea_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    trading_thesis TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'reviewed', 'actioned', 'expired', 'rejected')),
    expires_at DATETIME,

    FOREIGN KEY (event_id) REFERENCES news_events(event_id) ON DELETE CASCADE
);

-- Index for finding new trading ideas
CREATE INDEX idx_ideas_status
ON trading_ideas(status, generated_at DESC);

-- Index for finding ideas by event
CREATE INDEX idx_ideas_event
ON trading_ideas(event_id, status);

-- Index for expiration cleanup
CREATE INDEX idx_ideas_expiration
ON trading_ideas(expires_at)
WHERE expires_at IS NOT NULL AND status = 'new';

-- ============================================================================
-- TRADE STRATEGIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS trade_strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    strategy_type TEXT NOT NULL CHECK(strategy_type IN ('momentum', 'reversal', 'pairs', 'options', 'futures')),
    ticker TEXT NOT NULL,
    entry_conditions TEXT NOT NULL,
    exit_target_profit REAL,
    exit_target_loss REAL,
    time_horizon TEXT CHECK(time_horizon IN ('intraday', 'swing', 'position', 'long-term')),
    position_size_pct REAL DEFAULT 1.0,
    risk_reward_ratio REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'active', 'closed', 'cancelled')),

    FOREIGN KEY (idea_id) REFERENCES trading_ideas(idea_id) ON DELETE CASCADE
);

-- Index for finding strategies by idea
CREATE INDEX idx_strategies_idea
ON trade_strategies(idea_id, status);

-- Index for finding strategies by ticker
CREATE INDEX idx_strategies_ticker
ON trade_strategies(ticker, status, created_at DESC);

-- Index for finding strategies by type
CREATE INDEX idx_strategies_type
ON trade_strategies(strategy_type, status);

-- ============================================================================
-- METADATA TABLE (System Configuration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default retention policy
INSERT OR IGNORE INTO system_metadata (key, value) VALUES
    ('data_retention_hours', '24'),
    ('event_stale_threshold_hours', '6'),
    ('last_cleanup_run', datetime('now')),
    ('schema_version', '1.0.0');

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update news_events.article_count when articles are mapped
CREATE TRIGGER IF NOT EXISTS trg_update_event_article_count_insert
AFTER INSERT ON event_articles
BEGIN
    UPDATE news_events
    SET article_count = article_count + 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE event_id = NEW.event_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_update_event_article_count_delete
AFTER DELETE ON event_articles
BEGIN
    UPDATE news_events
    SET article_count = article_count - 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE event_id = OLD.event_id;
END;

-- Update rss_feeds.updated_at on modification
CREATE TRIGGER IF NOT EXISTS trg_update_feeds_timestamp
AFTER UPDATE ON rss_feeds
BEGIN
    UPDATE rss_feeds
    SET updated_at = CURRENT_TIMESTAMP
    WHERE feed_id = NEW.feed_id;
END;

-- Mark old events as stale automatically
CREATE TRIGGER IF NOT EXISTS trg_mark_stale_events
AFTER UPDATE ON news_events
WHEN NEW.last_updated < datetime('now', '-6 hours') AND NEW.status = 'active'
BEGIN
    UPDATE news_events
    SET status = 'stale'
    WHERE event_id = NEW.event_id;
END;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Active events ranked by importance
CREATE VIEW IF NOT EXISTS v_active_events_ranked AS
SELECT
    e.event_id,
    e.event_summary,
    e.first_reported_time,
    e.last_updated,
    e.source_count,
    e.article_count,
    e.relevance_score,
    ROUND((julianday('now') - julianday(e.first_reported_time)) * 24, 2) AS hours_old,
    COUNT(ti.idea_id) AS trading_ideas_count
FROM news_events e
LEFT JOIN trading_ideas ti ON e.event_id = ti.event_id AND ti.status = 'new'
WHERE e.status = 'active'
GROUP BY e.event_id
ORDER BY e.source_count DESC, e.first_reported_time DESC;

-- View: Pending articles ready for processing
CREATE VIEW IF NOT EXISTS v_pending_articles AS
SELECT
    a.article_id,
    a.headline,
    a.source,
    a.publish_datetime,
    a.url,
    f.source_name,
    f.category,
    ROUND((julianday('now') - julianday(a.publish_datetime)) * 24, 2) AS hours_old
FROM articles a
JOIN rss_feeds f ON a.feed_id = f.feed_id
WHERE a.processed_status = 'pending'
ORDER BY a.publish_datetime DESC;

-- View: Trading ideas with strategy counts
CREATE VIEW IF NOT EXISTS v_trading_ideas_summary AS
SELECT
    ti.idea_id,
    ti.headline,
    ti.summary,
    ti.trading_thesis,
    ti.confidence_score,
    ti.generated_at,
    ti.status,
    e.event_summary,
    e.source_count,
    COUNT(ts.strategy_id) AS strategy_count
FROM trading_ideas ti
JOIN news_events e ON ti.event_id = e.event_id
LEFT JOIN trade_strategies ts ON ti.idea_id = ts.idea_id
GROUP BY ti.idea_id
ORDER BY ti.generated_at DESC;

-- ============================================================================
-- PERFORMANCE ANALYSIS
-- ============================================================================

-- Run ANALYZE after bulk inserts to update query planner statistics
-- ANALYZE;
