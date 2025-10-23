"""News Event models for clustering"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class NewsEvent(Base):
    """Grouped news event (cluster of related articles)"""

    __tablename__ = "news_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    event_summary = Column(Text, nullable=False)
    event_key = Column(String(200), index=True)  # normalized key for grouping

    first_reported_time = Column(DateTime, nullable=False, index=True)
    last_updated = Column(DateTime, nullable=False, index=True)

    source_count = Column(Integer, default=1)
    article_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0, index=True)

    status = Column(
        String(20),
        default="active",
        index=True
    )  # active, stale, archived

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    articles = relationship("EventArticle", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_events_active_ranked", "status", "source_count", "first_reported_time"),
        Index("idx_events_timerange", "first_reported_time", "status"),
    )

    def __repr__(self):
        return f"<NewsEvent(event_id={self.event_id}, summary='{self.event_summary[:50]}...')>"


class EventArticle(Base):
    """Many-to-many relationship between events and articles"""

    __tablename__ = "event_articles"

    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("news_events.event_id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.article_id", ondelete="CASCADE"), nullable=False)
    contribution_score = Column(Float, default=1.0)
    added_at = Column(DateTime, server_default=func.now())

    # Relationships
    event = relationship("NewsEvent", back_populates="articles")
    article = relationship("Article", backref="event_mappings")

    __table_args__ = (
        Index("idx_event_articles_event", "event_id", "added_at"),
        Index("idx_event_articles_article", "article_id"),
    )
