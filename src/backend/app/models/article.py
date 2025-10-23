"""Article model"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Article(Base):
    """News article from RSS feeds"""

    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    feed_id = Column(Integer, ForeignKey("rss_feeds.feed_id", ondelete="CASCADE"), nullable=False)

    headline = Column(Text, nullable=False)
    url = Column(String(1000), unique=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    publish_datetime = Column(DateTime, nullable=False, index=True)

    processed_status = Column(
        String(20),
        default="pending",
        index=True,
        nullable=False
    )  # pending, processing, processed, failed, duplicate

    content_hash = Column(String(64), index=True)  # for duplicate detection
    raw_content = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    feed = relationship("RSSFeed", backref="articles")

    __table_args__ = (
        Index("idx_articles_processing", "processed_status", "publish_datetime"),
        Index("idx_articles_recent", "publish_datetime"),
    )

    def __repr__(self):
        return f"<Article(article_id={self.article_id}, headline='{self.headline[:50]}...')>"
