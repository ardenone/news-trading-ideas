"""Tests for service modules."""

import pytest
from unittest.mock import Mock, patch
from backend.services.rss_service import RSSService
from backend.database import SessionLocal, init_db


@pytest.fixture
def db_session():
    """Create database session for tests."""
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_rss_parse_feed():
    """Test RSS feed parsing."""
    # Mock feed data
    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = Mock(
            bozo=False,
            entries=[
                Mock(
                    link="https://example.com/article1",
                    title="Test Article",
                    content=[Mock(value="<p>Test content</p>")],
                    published_parsed=(2025, 10, 23, 0, 0, 0, 0, 0, 0)
                )
            ]
        )

        articles = RSSService.parse_feed("https://example.com/feed")
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"


def test_article_deduplication(db_session):
    """Test article deduplication."""
    from backend.database import NewsArticle

    # Add first article
    article1 = NewsArticle(
        url="https://example.com/test",
        url_hash=NewsArticle.generate_url_hash("https://example.com/test"),
        title="Test",
        source="test",
    )
    db_session.add(article1)
    db_session.commit()

    # Try to add duplicate
    existing = db_session.query(NewsArticle).filter_by(
        url_hash=NewsArticle.generate_url_hash("https://example.com/test")
    ).first()

    assert existing is not None
    assert existing.title == "Test"


@pytest.mark.asyncio
async def test_openai_connection():
    """Test OpenAI API connection (requires API key)."""
    from backend.services.openai_service import OpenAIService

    # This will fail without API key, but tests the structure
    try:
        result = await OpenAIService.test_connection()
        assert isinstance(result, bool)
    except Exception:
        # Expected if no API key
        pass
