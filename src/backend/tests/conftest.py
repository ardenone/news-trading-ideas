"""Pytest configuration and fixtures"""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import RSSFeed, Article, NewsEvent, TradingIdea


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_feed(db_session):
    """Create sample RSS feed"""
    feed = RSSFeed(
        feed_url="https://example.com/rss",
        source_name="Example News",
        category="finance",
        update_interval=300,
        is_active=True,
    )
    db_session.add(feed)
    await db_session.commit()
    await db_session.refresh(feed)
    return feed


@pytest_asyncio.fixture
async def sample_article(db_session, sample_feed):
    """Create sample article"""
    article = Article(
        feed_id=sample_feed.feed_id,
        headline="Test Article Headline",
        url="https://example.com/article/123",
        source="Example News",
        publish_datetime="2025-10-22T14:30:00",
        processed_status="pending",
        content_hash="abc123",
    )
    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article)
    return article
