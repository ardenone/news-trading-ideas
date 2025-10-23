"""RSS Feed model"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class RSSFeed(Base):
    """RSS Feed configuration and metadata"""

    __tablename__ = "rss_feeds"

    feed_id = Column(Integer, primary_key=True, autoincrement=True)
    feed_url = Column(String(500), unique=True, nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    category = Column(String(50), default="general", index=True)
    update_interval = Column(Integer, default=300)  # seconds between updates
    last_fetched = Column(DateTime, nullable=True)
    next_fetch_scheduled = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RSSFeed(feed_id={self.feed_id}, source_name='{self.source_name}')>"
