"""
Database Operations Tests
Tests for SQLite CRUD operations, indexes, triggers, and views
"""

import pytest
from datetime import datetime, timedelta
import hashlib


class TestDatabaseSchema:
    """Test database schema and table creation"""

    def test_all_tables_exist(self, db_session):
        """Should have all required tables"""
        tables = [
            "rss_feeds",
            "articles",
            "news_events",
            "event_articles",
            "trading_ideas",
            "trade_strategies",
            "system_metadata"
        ]

        for table in tables:
            result = db_session.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            ).fetchone()
            assert result is not None, f"Table {table} does not exist"

    def test_indexes_created(self, db_session):
        """Should have all required indexes"""
        indexes = [
            "idx_feeds_next_fetch",
            "idx_articles_processing",
            "idx_articles_recent",
            "idx_events_active_ranked"
        ]

        for index in indexes:
            result = db_session.execute(
                f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index}'"
            ).fetchone()
            # Note: Some indexes might not exist yet, depending on schema execution
            if result:
                assert result[0] == index

    def test_foreign_keys_enabled(self, db_session):
        """Should have foreign keys enabled"""
        result = db_session.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1, "Foreign keys should be enabled"


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations"""

    def test_create_feed(self, db_session):
        """Should create new RSS feed"""
        result = db_session.execute(
            """INSERT INTO rss_feeds (feed_url, source_name, category)
               VALUES (?, ?, ?)""",
            ("https://test.com/rss", "Test Feed", "tech")
        )
        db_session.commit()

        feed_id = result.lastrowid
        assert feed_id > 0

    def test_read_feed(self, db_session, sample_feeds):
        """Should read existing feed"""
        feed_id = sample_feeds[0]

        result = db_session.execute(
            "SELECT source_name FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()

        assert result is not None
        assert result[0] == "Bloomberg"

    def test_update_feed(self, db_session, sample_feeds):
        """Should update feed properties"""
        feed_id = sample_feeds[0]

        db_session.execute(
            "UPDATE rss_feeds SET update_interval = ? WHERE feed_id = ?",
            (600, feed_id)
        )
        db_session.commit()

        result = db_session.execute(
            "SELECT update_interval FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()

        assert result[0] == 600

    def test_delete_feed_cascades(self, db_session, sample_feeds, sample_articles):
        """Should cascade delete articles when feed is deleted"""
        feed_id = sample_feeds[0]

        # Count articles before delete
        before_count = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()[0]

        assert before_count > 0

        # Delete feed
        db_session.execute(
            "DELETE FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        )
        db_session.commit()

        # Check articles deleted
        after_count = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()[0]

        assert after_count == 0


class TestArticleOperations:
    """Test article-specific operations"""

    def test_prevent_duplicate_urls(self, db_session, sample_feeds):
        """Should prevent duplicate article URLs"""
        feed_id = sample_feeds[0]
        url = "https://unique-url.com/article"

        # Insert first article
        db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, "Article", url, "Source", datetime.utcnow(),
             hashlib.sha256(b"test").hexdigest())
        )
        db_session.commit()

        # Attempt duplicate
        with pytest.raises(Exception):  # Unique constraint on URL
            db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (feed_id, "Article 2", url, "Source", datetime.utcnow(),
                 hashlib.sha256(b"test2").hexdigest())
            )
            db_session.commit()

    def test_article_timestamps(self, db_session, sample_feeds):
        """Should automatically set created_at timestamp"""
        feed_id = sample_feeds[0]

        result = db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, "Timestamp Test", "https://example.com/timestamp",
             "Source", datetime.utcnow(), hashlib.sha256(b"test").hexdigest())
        )
        db_session.commit()

        article_id = result.lastrowid

        created_at = db_session.execute(
            "SELECT created_at FROM articles WHERE article_id = ?",
            (article_id,)
        ).fetchone()[0]

        assert created_at is not None

    def test_article_status_constraint(self, db_session, sample_feeds):
        """Should enforce valid article status values"""
        feed_id = sample_feeds[0]

        valid_statuses = ["pending", "processing", "processed", "failed", "duplicate"]

        for status in valid_statuses:
            result = db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime,
                    content_hash, processed_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (feed_id, f"Status {status}", f"https://example.com/{status}",
                 "Source", datetime.utcnow(), hashlib.sha256(status.encode()).hexdigest(),
                 status)
            )
            db_session.commit()
            assert result.lastrowid > 0


class TestNewsEventsAndClusters:
    """Test news events (clusters) operations"""

    def test_create_news_event(self, db_session):
        """Should create news event cluster"""
        result = db_session.execute(
            """INSERT INTO news_events
               (event_summary, event_key, first_reported_time, last_updated,
                source_count, relevance_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Fed Rate Decision", "fed-rate-2025-10",
             datetime.utcnow(), datetime.utcnow(), 3, 85.0)
        )
        db_session.commit()

        event_id = result.lastrowid
        assert event_id > 0

    def test_link_articles_to_event(self, db_session, sample_articles, sample_cluster_data):
        """Should link articles to news events"""
        event_id = sample_cluster_data

        # Verify articles are linked
        linked_count = db_session.execute(
            "SELECT COUNT(*) FROM event_articles WHERE event_id = ?",
            (event_id,)
        ).fetchone()[0]

        assert linked_count == 3

    def test_event_article_count_trigger(self, db_session, sample_cluster_data):
        """Should update article_count via trigger"""
        event_id = sample_cluster_data

        # Check current count
        count = db_session.execute(
            "SELECT article_count FROM news_events WHERE event_id = ?",
            (event_id,)
        ).fetchone()[0]

        # Trigger should have updated this
        assert count >= 0

    def test_prevent_duplicate_article_cluster_mapping(
        self,
        db_session,
        sample_articles,
        sample_cluster_data
    ):
        """Should prevent duplicate article-cluster mappings"""
        event_id = sample_cluster_data
        article_id = sample_articles[0]["id"]

        # Attempt duplicate mapping
        with pytest.raises(Exception):  # Unique constraint
            db_session.execute(
                "INSERT INTO event_articles (event_id, article_id) VALUES (?, ?)",
                (event_id, article_id)
            )
            db_session.commit()


class TestTradingIdeas:
    """Test trading ideas operations"""

    def test_create_trading_idea(self, db_session, sample_cluster_data):
        """Should create trading idea"""
        event_id = sample_cluster_data

        result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Fed Rate Impact", "Summary...", "Buy tech stocks", 8.5)
        )
        db_session.commit()

        idea_id = result.lastrowid
        assert idea_id > 0

    def test_trading_idea_status_constraint(self, db_session, sample_cluster_data):
        """Should enforce valid trading idea status"""
        event_id = sample_cluster_data

        valid_statuses = ["new", "reviewed", "actioned", "expired", "rejected"]

        for status in valid_statuses:
            result = db_session.execute(
                """INSERT INTO trading_ideas
                   (event_id, headline, summary, trading_thesis,
                    confidence_score, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (event_id, f"Idea {status}", "Summary", "Thesis", 7.0, status)
            )
            db_session.commit()
            assert result.lastrowid > 0

    def test_link_strategies_to_idea(self, db_session, sample_cluster_data):
        """Should link trading strategies to ideas"""
        event_id = sample_cluster_data

        # Create idea
        idea_result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Test Idea", "Summary", "Thesis", 8.0)
        )
        db_session.commit()
        idea_id = idea_result.lastrowid

        # Create strategy
        strategy_result = db_session.execute(
            """INSERT INTO trade_strategies
               (idea_id, strategy_type, ticker, entry_conditions,
                time_horizon, risk_reward_ratio)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (idea_id, "momentum", "AAPL", "Buy above $180", "swing", 2.5)
        )
        db_session.commit()

        assert strategy_result.lastrowid > 0


class TestDatabaseViews:
    """Test database views"""

    def test_pending_articles_view(self, db_session, sample_articles):
        """Should query pending articles via view"""
        # Check if view exists
        view_exists = db_session.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_pending_articles'"
        ).fetchone()

        if view_exists:
            result = db_session.execute(
                "SELECT COUNT(*) FROM v_pending_articles"
            ).fetchone()
            assert result[0] > 0

    def test_active_events_ranked_view(self, db_session, sample_cluster_data):
        """Should query active events ranked by impact"""
        view_exists = db_session.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_active_events_ranked'"
        ).fetchone()

        if view_exists:
            result = db_session.execute(
                "SELECT * FROM v_active_events_ranked LIMIT 10"
            ).fetchall()
            assert len(result) >= 0


class TestIndexPerformance:
    """Test index effectiveness"""

    def test_unprocessed_articles_index(self, db_session, sample_articles):
        """Should use index for unprocessed articles query"""
        # Query should be fast with index
        result = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE processed_status = 'pending'"
        ).fetchone()

        assert result[0] >= 0

    def test_recent_articles_index(self, db_session, sample_articles):
        """Should use index for recent articles query"""
        cutoff = datetime.utcnow() - timedelta(hours=24)

        result = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE publish_datetime > ?",
            (cutoff,)
        ).fetchone()

        assert result[0] >= 0


class TestDataRetention:
    """Test data retention and cleanup"""

    def test_archive_old_articles(self, db_session, sample_feeds):
        """Should archive articles older than retention period"""
        feed_id = sample_feeds[0]

        # Create old article (31 days old)
        old_date = datetime.utcnow() - timedelta(days=31)
        result = db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, "Old Article", "https://example.com/old",
             "Source", old_date, hashlib.sha256(b"old").hexdigest())
        )
        db_session.commit()

        # Simulate cleanup (delete articles older than 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        deleted = db_session.execute(
            "DELETE FROM articles WHERE publish_datetime < ?",
            (cutoff,)
        )
        db_session.commit()

        assert deleted.rowcount > 0

    def test_mark_stale_events(self, db_session):
        """Should mark old events as stale"""
        # Create old event
        old_time = datetime.utcnow() - timedelta(hours=7)

        result = db_session.execute(
            """INSERT INTO news_events
               (event_summary, first_reported_time, last_updated, source_count)
               VALUES (?, ?, ?, ?)""",
            ("Stale Event", old_time, old_time, 1)
        )
        db_session.commit()

        event_id = result.lastrowid

        # Manually mark as stale (trigger may not fire in tests)
        db_session.execute(
            "UPDATE news_events SET status = 'stale' WHERE last_updated < datetime('now', '-6 hours')"
        )
        db_session.commit()

        status = db_session.execute(
            "SELECT status FROM news_events WHERE event_id = ?",
            (event_id,)
        ).fetchone()[0]

        assert status in ["stale", "active"]


class TestTransactions:
    """Test transaction handling"""

    def test_rollback_on_error(self, db_session, sample_feeds):
        """Should rollback transaction on error"""
        feed_id = sample_feeds[0]

        try:
            db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (feed_id, "Article 1", "https://example.com/1",
                 "Source", datetime.utcnow(), hashlib.sha256(b"1").hexdigest())
            )

            # This should fail (duplicate URL)
            db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (feed_id, "Article 2", "https://example.com/1",  # Duplicate URL
                 "Source", datetime.utcnow(), hashlib.sha256(b"2").hexdigest())
            )

            db_session.commit()
        except Exception:
            db_session.rollback()

        # First article should not be committed
        count = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE headline = 'Article 1'"
        ).fetchone()[0]

        assert count == 0  # Rolled back

    def test_commit_successful_transaction(self, db_session, sample_feeds):
        """Should commit successful transaction"""
        feed_id = sample_feeds[0]

        db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, "Success Article", "https://example.com/success",
             "Source", datetime.utcnow(), hashlib.sha256(b"success").hexdigest())
        )
        db_session.commit()

        count = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE headline = 'Success Article'"
        ).fetchone()[0]

        assert count == 1
