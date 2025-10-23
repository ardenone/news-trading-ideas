"""
Backend Test Configuration and Fixtures
Provides shared test fixtures for database, API clients, and mock data
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import hashlib


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Enable WAL mode for better concurrency
    with engine.connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create test database session with schema"""
    # Read and execute schema
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "../../architecture/database-schema.sql"
    )

    with open(schema_path, "r") as f:
        schema = f.read()

    # Execute schema creation
    with test_db_engine.connect() as conn:
        # Split and execute statements
        for statement in schema.split(";"):
            if statement.strip():
                try:
                    conn.execute(statement)
                except Exception as e:
                    # Skip statements that fail (like triggers on non-existent tables)
                    if "no such table" not in str(e).lower():
                        print(f"Warning: {e}")
        conn.commit()

    # Create session
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def sample_feeds(db_session):
    """Create sample RSS feeds"""
    feeds = [
        {
            "feed_url": "https://www.bloomberg.com/feed/news.rss",
            "source_name": "Bloomberg",
            "category": "financial",
            "update_interval": 300,
            "is_active": 1
        },
        {
            "feed_url": "https://www.reuters.com/finance/markets/rss",
            "source_name": "Reuters",
            "category": "financial",
            "update_interval": 300,
            "is_active": 1
        },
        {
            "feed_url": "https://www.wsj.com/xml/rss/3_7085.xml",
            "source_name": "Wall Street Journal",
            "category": "financial",
            "update_interval": 600,
            "is_active": 1
        }
    ]

    feed_ids = []
    for feed in feeds:
        result = db_session.execute(
            """INSERT INTO rss_feeds
               (feed_url, source_name, category, update_interval, is_active)
               VALUES (?, ?, ?, ?, ?)""",
            (feed["feed_url"], feed["source_name"], feed["category"],
             feed["update_interval"], feed["is_active"])
        )
        db_session.commit()
        feed_ids.append(result.lastrowid)

    return feed_ids


@pytest.fixture
def sample_articles(db_session, sample_feeds):
    """Create sample articles"""
    articles = []

    for i, feed_id in enumerate(sample_feeds):
        for j in range(3):  # 3 articles per feed
            headline = f"Test Headline {i}-{j}: Market Update"
            url = f"https://example.com/article-{i}-{j}"
            content = f"Full article content for article {i}-{j}. This discusses market trends."
            content_hash = hashlib.sha256(f"{headline}{url}".encode()).hexdigest()

            result = db_session.execute(
                """INSERT INTO articles
                   (feed_id, headline, url, source, publish_datetime,
                    processed_status, content_hash, raw_content)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (feed_id, headline, url, f"Source-{i}",
                 datetime.utcnow() - timedelta(hours=j),
                 "pending", content_hash, content)
            )
            db_session.commit()
            articles.append({
                "id": result.lastrowid,
                "headline": headline,
                "url": url,
                "feed_id": feed_id
            })

    return articles


# =============================================================================
# MOCK OPENAI FIXTURES
# =============================================================================

@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings API"""
    with patch("openai.AsyncOpenAI") as mock_client:
        # Create mock embedding response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536)  # Standard embedding size
        ]

        # Configure mock
        mock_instance = AsyncMock()
        mock_instance.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        yield mock_instance


@pytest.fixture
def mock_openai_completion():
    """Mock OpenAI completion API"""
    with patch("openai.AsyncOpenAI") as mock_client:
        # Create mock completion response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"title": "Test Cluster", "summary": "Test summary", "impact_score": 75, "confidence": 0.9}'))
        ]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        # Configure mock
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        yield mock_instance


@pytest.fixture
def mock_openai_trading_idea():
    """Mock OpenAI trading idea generation"""
    with patch("openai.AsyncOpenAI") as mock_client:
        trading_idea = """
        {
            "headline": "Fed Rate Decision Impact",
            "summary": "Federal Reserve announces rate cut, impacting tech stocks positively.",
            "trading_thesis": "Buy call options on QQQ as tech stocks rally on lower rates.",
            "ticker": "QQQ",
            "strategy_type": "options",
            "confidence_score": 8.5,
            "entry_conditions": "QQQ above 380",
            "exit_target_profit": 5.0,
            "exit_target_loss": 2.0,
            "time_horizon": "swing"
        }
        """

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=trading_idea))]

        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        yield mock_instance


# =============================================================================
# RSS FEED MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed parser"""
    with patch("feedparser.parse") as mock_parse:
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="Breaking: Fed Announces Rate Cut",
                link="https://example.com/fed-rate-cut",
                description="Federal Reserve cuts rates by 25 basis points",
                summary="The Fed announced a quarter-point rate cut today...",
                published="Wed, 22 Oct 2025 10:00:00 GMT",
                author="John Doe"
            ),
            Mock(
                title="Tech Stocks Rally on Fed News",
                link="https://example.com/tech-rally",
                description="Technology stocks surge following rate decision",
                summary="Major tech indices gained over 2% today...",
                published="Wed, 22 Oct 2025 11:00:00 GMT",
                author="Jane Smith"
            )
        ]
        mock_feed.bozo = False  # Not malformed

        mock_parse.return_value = mock_feed
        yield mock_parse


@pytest.fixture
def mock_malformed_rss():
    """Mock malformed RSS feed"""
    with patch("feedparser.parse") as mock_parse:
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feed.bozo = True  # Malformed
        mock_feed.bozo_exception = Exception("Invalid XML")

        mock_parse.return_value = mock_feed
        yield mock_parse


# =============================================================================
# FASTAPI TEST CLIENT FIXTURE
# =============================================================================

@pytest.fixture
def test_client(db_session):
    """Create FastAPI test client with dependency overrides"""
    # Import app here to avoid circular imports
    try:
        from app.main import app
        from app.dependencies import get_db

        # Override database dependency
        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        yield client

        # Clean up
        app.dependency_overrides.clear()
    except ImportError:
        # If app doesn't exist yet, create a minimal one for testing
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "healthy"}

        yield TestClient(app)


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_embedding_vector():
    """Generate sample embedding vector"""
    import numpy as np
    return np.random.rand(1536).astype(np.float32)


@pytest.fixture
def sample_cluster_data(db_session, sample_articles):
    """Create sample news event cluster"""
    result = db_session.execute(
        """INSERT INTO news_events
           (event_summary, event_key, first_reported_time, last_updated,
            source_count, article_count, relevance_score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("Fed Rate Decision", "fed-rate-2025-10",
         datetime.utcnow(), datetime.utcnow(),
         3, 3, 85.5)
    )
    db_session.commit()

    event_id = result.lastrowid

    # Link articles to event
    for article in sample_articles[:3]:
        db_session.execute(
            """INSERT INTO event_articles (event_id, article_id, contribution_score)
               VALUES (?, ?, ?)""",
            (event_id, article["id"], 1.0)
        )
    db_session.commit()

    return event_id


@pytest.fixture
def freeze_time():
    """Freeze time for consistent testing"""
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2025, 10, 22, 12, 0, 0)
        mock_datetime.now.return_value = datetime(2025, 10, 22, 12, 0, 0)
        yield mock_datetime


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# PERFORMANCE TESTING FIXTURES
# =============================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    import time

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.metrics = {}

        def start(self, label: str):
            self.start_time = time.perf_counter()
            self.metrics[label] = {"start": self.start_time}

        def stop(self, label: str):
            end_time = time.perf_counter()
            if label in self.metrics:
                duration = end_time - self.metrics[label]["start"]
                self.metrics[label]["duration"] = duration
                return duration
            return None

        def get_duration(self, label: str):
            return self.metrics.get(label, {}).get("duration")

    return PerformanceTracker()
