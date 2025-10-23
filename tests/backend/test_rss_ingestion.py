"""
RSS Ingestion Service Tests
Tests for RSS feed parsing, deduplication, and article storage
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import feedparser


class TestRSSFeedParsing:
    """Test RSS feed parsing functionality"""

    def test_parse_valid_rss_feed(self, mock_rss_feed, db_session):
        """Should successfully parse valid RSS feed"""
        feed = feedparser.parse("https://example.com/rss")

        assert feed.bozo == False
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "Breaking: Fed Announces Rate Cut"
        assert "example.com/fed-rate-cut" in feed.entries[0].link

    def test_handle_malformed_rss(self, mock_malformed_rss):
        """Should handle malformed RSS gracefully"""
        feed = feedparser.parse("https://example.com/bad-rss")

        assert feed.bozo == True
        assert len(feed.entries) == 0

    def test_extract_article_fields(self, mock_rss_feed):
        """Should extract all required article fields"""
        feed = feedparser.parse("https://example.com/rss")
        entry = feed.entries[0]

        assert hasattr(entry, "title")
        assert hasattr(entry, "link")
        assert hasattr(entry, "description")
        assert hasattr(entry, "published")

    def test_handle_missing_fields(self):
        """Should handle missing optional fields gracefully"""
        with patch("feedparser.parse") as mock_parse:
            mock_feed = Mock()
            mock_feed.entries = [
                Mock(
                    title="Test",
                    link="https://example.com/test",
                    description="Test description"
                    # Missing: published, author, summary
                )
            ]
            mock_feed.bozo = False
            mock_parse.return_value = mock_feed

            feed = feedparser.parse("https://example.com/rss")
            entry = feed.entries[0]

            assert entry.title == "Test"
            assert not hasattr(entry, "published")


class TestArticleDeduplication:
    """Test article deduplication logic"""

    def test_generate_content_hash(self):
        """Should generate consistent content hash"""
        title = "Test Article Title"
        url = "https://example.com/article"

        hash1 = hashlib.sha256(f"{title}{url}".encode()).hexdigest()
        hash2 = hashlib.sha256(f"{title}{url}".encode()).hexdigest()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-char hex string

    def test_detect_duplicate_article(self, db_session, sample_feeds):
        """Should detect duplicate articles by content hash"""
        feed_id = sample_feeds[0]

        # Insert first article
        headline = "Duplicate Test Article"
        url = "https://example.com/duplicate"
        content_hash = hashlib.sha256(f"{headline}{url}".encode()).hexdigest()

        db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed_id, headline, url, "Test Source", datetime.utcnow(), content_hash)
        )
        db_session.commit()

        # Check for duplicate
        result = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()

        assert result[0] == 1

        # Attempt to insert duplicate (should be prevented by unique constraint)
        with pytest.raises(Exception):  # Unique constraint violation
            db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (feed_id, headline, url, "Test Source", datetime.utcnow(), content_hash)
            )
            db_session.commit()

    def test_allow_different_articles(self, db_session, sample_feeds):
        """Should allow articles with different content"""
        feed_id = sample_feeds[0]

        articles = [
            ("Article 1", "https://example.com/1"),
            ("Article 2", "https://example.com/2"),
            ("Article 3", "https://example.com/3")
        ]

        for headline, url in articles:
            content_hash = hashlib.sha256(f"{headline}{url}".encode()).hexdigest()
            db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (feed_id, headline, url, "Test Source", datetime.utcnow(), content_hash)
            )
        db_session.commit()

        result = db_session.execute("SELECT COUNT(*) FROM articles").fetchone()
        assert result[0] == 3


class TestArticleStorage:
    """Test article database storage"""

    def test_store_article_all_fields(self, db_session, sample_feeds):
        """Should store article with all fields"""
        feed_id = sample_feeds[0]

        article_data = {
            "headline": "Complete Article Test",
            "url": "https://example.com/complete",
            "source": "Test Source",
            "raw_content": "Full article content here...",
            "content_hash": hashlib.sha256(b"test").hexdigest(),
            "publish_datetime": datetime.utcnow(),
            "processed_status": "pending"
        }

        result = db_session.execute(
            """INSERT INTO articles
               (feed_id, headline, url, source, raw_content, content_hash,
                publish_datetime, processed_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (feed_id, article_data["headline"], article_data["url"],
             article_data["source"], article_data["raw_content"],
             article_data["content_hash"], article_data["publish_datetime"],
             article_data["processed_status"])
        )
        db_session.commit()

        article_id = result.lastrowid

        # Retrieve and verify
        stored = db_session.execute(
            "SELECT * FROM articles WHERE article_id = ?",
            (article_id,)
        ).fetchone()

        assert stored is not None
        assert stored[2] == article_data["headline"]  # headline column
        assert stored[3] == article_data["url"]  # url column

    def test_article_status_tracking(self, db_session, sample_articles):
        """Should track article processing status"""
        article_id = sample_articles[0]["id"]

        # Check initial status
        status = db_session.execute(
            "SELECT processed_status FROM articles WHERE article_id = ?",
            (article_id,)
        ).fetchone()[0]
        assert status == "pending"

        # Update status
        db_session.execute(
            "UPDATE articles SET processed_status = ? WHERE article_id = ?",
            ("processing", article_id)
        )
        db_session.commit()

        # Verify update
        status = db_session.execute(
            "SELECT processed_status FROM articles WHERE article_id = ?",
            (article_id,)
        ).fetchone()[0]
        assert status == "processing"

    def test_fetch_unprocessed_articles(self, db_session, sample_articles):
        """Should fetch only unprocessed articles"""
        # All sample articles start as 'pending'
        pending = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE processed_status = 'pending'"
        ).fetchone()[0]

        assert pending == len(sample_articles)

        # Mark one as processed
        db_session.execute(
            "UPDATE articles SET processed_status = 'processed' WHERE article_id = ?",
            (sample_articles[0]["id"],)
        )
        db_session.commit()

        # Recheck
        pending = db_session.execute(
            "SELECT COUNT(*) FROM articles WHERE processed_status = 'pending'"
        ).fetchone()[0]

        assert pending == len(sample_articles) - 1


class TestFeedManagement:
    """Test RSS feed management"""

    def test_add_new_feed(self, db_session):
        """Should add new RSS feed"""
        feed_data = {
            "feed_url": "https://new-feed.com/rss",
            "source_name": "New Feed",
            "category": "tech",
            "update_interval": 300,
            "is_active": 1
        }

        result = db_session.execute(
            """INSERT INTO rss_feeds
               (feed_url, source_name, category, update_interval, is_active)
               VALUES (?, ?, ?, ?, ?)""",
            (feed_data["feed_url"], feed_data["source_name"],
             feed_data["category"], feed_data["update_interval"],
             feed_data["is_active"])
        )
        db_session.commit()

        feed_id = result.lastrowid
        assert feed_id > 0

    def test_update_feed_schedule(self, db_session, sample_feeds):
        """Should update feed fetch schedule"""
        feed_id = sample_feeds[0]

        new_time = datetime.utcnow() + timedelta(minutes=5)
        db_session.execute(
            "UPDATE rss_feeds SET next_fetch_scheduled = ? WHERE feed_id = ?",
            (new_time, feed_id)
        )
        db_session.commit()

        scheduled = db_session.execute(
            "SELECT next_fetch_scheduled FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()[0]

        assert scheduled is not None

    def test_disable_feed(self, db_session, sample_feeds):
        """Should disable/enable feeds"""
        feed_id = sample_feeds[0]

        # Disable
        db_session.execute(
            "UPDATE rss_feeds SET is_active = 0 WHERE feed_id = ?",
            (feed_id,)
        )
        db_session.commit()

        is_active = db_session.execute(
            "SELECT is_active FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()[0]
        assert is_active == 0

        # Re-enable
        db_session.execute(
            "UPDATE rss_feeds SET is_active = 1 WHERE feed_id = ?",
            (feed_id,)
        )
        db_session.commit()

        is_active = db_session.execute(
            "SELECT is_active FROM rss_feeds WHERE feed_id = ?",
            (feed_id,)
        ).fetchone()[0]
        assert is_active == 1


class TestErrorHandling:
    """Test error handling in RSS ingestion"""

    def test_handle_network_timeout(self):
        """Should handle network timeouts gracefully"""
        with patch("feedparser.parse") as mock_parse:
            mock_parse.side_effect = TimeoutError("Connection timeout")

            with pytest.raises(TimeoutError):
                feedparser.parse("https://example.com/rss")

    def test_handle_invalid_url(self):
        """Should handle invalid URLs"""
        with patch("feedparser.parse") as mock_parse:
            mock_feed = Mock()
            mock_feed.entries = []
            mock_feed.bozo = True
            mock_parse.return_value = mock_feed

            feed = feedparser.parse("not-a-valid-url")
            assert len(feed.entries) == 0

    def test_handle_empty_feed(self):
        """Should handle feeds with no entries"""
        with patch("feedparser.parse") as mock_parse:
            mock_feed = Mock()
            mock_feed.entries = []
            mock_feed.bozo = False
            mock_parse.return_value = mock_feed

            feed = feedparser.parse("https://example.com/empty-rss")
            assert len(feed.entries) == 0


class TestPerformance:
    """Test performance requirements"""

    def test_bulk_article_insertion(self, db_session, sample_feeds, performance_tracker):
        """Should handle bulk article insertion efficiently"""
        feed_id = sample_feeds[0]

        performance_tracker.start("bulk_insert")

        # Insert 100 articles
        articles = []
        for i in range(100):
            headline = f"Performance Test Article {i}"
            url = f"https://example.com/perf-{i}"
            content_hash = hashlib.sha256(f"{headline}{url}".encode()).hexdigest()

            articles.append((
                feed_id, headline, url, "Test Source",
                datetime.utcnow(), "pending", content_hash, f"Content {i}"
            ))

        db_session.executemany(
            """INSERT INTO articles
               (feed_id, headline, url, source, publish_datetime,
                processed_status, content_hash, raw_content)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            articles
        )
        db_session.commit()

        duration = performance_tracker.stop("bulk_insert")

        # Should complete in less than 1 second
        assert duration < 1.0

        # Verify all inserted
        count = db_session.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count >= 100
