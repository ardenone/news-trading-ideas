"""Database models and connection management."""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import hashlib

from config import settings

# Database setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class NewsArticle(Base):
    """News article model."""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    url_hash = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(100), nullable=False)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    cluster_id = Column(Integer, ForeignKey("news_clusters.id"), nullable=True)
    embedding = Column(JSON)  # Store embedding vector

    # Relationship
    cluster = relationship("NewsCluster", back_populates="articles")

    @staticmethod
    def generate_url_hash(url: str) -> str:
        """Generate SHA256 hash of URL for deduplication."""
        return hashlib.sha256(url.encode()).hexdigest()


class NewsCluster(Base):
    """News cluster model."""
    __tablename__ = "news_clusters"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(500), nullable=False)
    summary = Column(Text)
    article_count = Column(Integer, default=0)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    articles = relationship("NewsArticle", back_populates="cluster")
    trading_ideas = relationship("TradingIdea", back_populates="cluster")


class TradingIdea(Base):
    """Trading idea model."""
    __tablename__ = "trading_ideas"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("news_clusters.id"), nullable=False)
    idea = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    instruments = Column(JSON)  # List of stocks, ETFs, etc.
    direction = Column(String(20), nullable=False)  # long, short, neutral
    time_horizon = Column(String(20))  # short, medium, long
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    cluster = relationship("NewsCluster", back_populates="trading_ideas")


class RSSSource(Base):
    """RSS feed source model."""
    __tablename__ = "rss_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    last_fetch = Column(DateTime)
    fetch_interval = Column(Integer, default=300)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)


# Database initialization
def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
