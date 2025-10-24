"""RSS feed ingestion service."""

import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging
from bs4 import BeautifulSoup
import hashlib

from database import NewsArticle, RSSSource
from config import settings

logger = logging.getLogger(__name__)


class RSSService:
    """Service for RSS feed ingestion and parsing."""

    @staticmethod
    def parse_feed(feed_url: str) -> List[Dict[str, Any]]:
        """Parse RSS feed and extract articles."""
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:  # Feed has errors
                logger.warning(f"Feed parse warning for {feed_url}: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries:
                article = RSSService._parse_entry(entry, feed_url)
                if article:
                    articles.append(article)

            logger.info(f"Parsed {len(articles)} articles from {feed_url}")
            return articles

        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            return []

    @staticmethod
    def _parse_entry(entry: Any, source_url: str) -> Optional[Dict[str, Any]]:
        """Parse individual feed entry."""
        try:
            # Extract URL
            url = entry.get("link", "")
            if not url:
                return None

            # Extract title
            title = entry.get("title", "Untitled")

            # Extract content
            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].value
            elif hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description

            # Clean HTML from content
            if content:
                soup = BeautifulSoup(content, "html.parser")
                content = soup.get_text(strip=True)

            # Extract published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])

            # Extract source name
            source_name = entry.get("source", {}).get("title", "")
            if not source_name:
                # Try to extract from feed URL
                from urllib.parse import urlparse
                parsed = urlparse(source_url)
                source_name = parsed.netloc

            return {
                "url": url,
                "title": title,
                "content": content,
                "source": source_name,
                "published_at": published_at
            }

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    @staticmethod
    def fetch_and_store(db: Session, source: RSSSource) -> Dict[str, Any]:
        """Fetch RSS feed and store new articles in database."""
        try:
            articles = RSSService.parse_feed(source.url)

            added_count = 0
            duplicate_count = 0

            for article_data in articles:
                # Check if article already exists
                url_hash = NewsArticle.generate_url_hash(article_data["url"])
                existing = db.query(NewsArticle).filter_by(url_hash=url_hash).first()

                if existing:
                    duplicate_count += 1
                    continue

                # Create new article
                article = NewsArticle(
                    url=article_data["url"],
                    url_hash=url_hash,
                    title=article_data["title"],
                    content=article_data["content"],
                    source=article_data["source"],
                    published_at=article_data.get("published_at")
                )
                db.add(article)
                added_count += 1

            # Update source last_fetch
            source.last_fetch = datetime.utcnow()
            db.commit()

            logger.info(
                f"RSS fetch complete for {source.name}: "
                f"{added_count} new, {duplicate_count} duplicates"
            )

            return {
                "source": source.name,
                "total_parsed": len(articles),
                "new_articles": added_count,
                "duplicates": duplicate_count,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error fetching RSS feed {source.name}: {e}")
            db.rollback()
            return {
                "source": source.name,
                "error": str(e),
                "success": False
            }

    @staticmethod
    def fetch_all_sources(db: Session) -> List[Dict[str, Any]]:
        """Fetch all enabled RSS sources."""
        sources = db.query(RSSSource).filter_by(enabled=True).all()
        results = []

        for source in sources:
            result = RSSService.fetch_and_store(db, source)
            results.append(result)

        return results

    @staticmethod
    def initialize_sources(db: Session) -> None:
        """Initialize RSS sources from config if not exists."""
        existing_urls = {source.url for source in db.query(RSSSource).all()}

        for feed_url in settings.rss_feed_list:
            if feed_url not in existing_urls:
                # Extract name from URL
                from urllib.parse import urlparse
                parsed = urlparse(feed_url)
                name = parsed.netloc.replace("www.", "")

                source = RSSSource(
                    name=name,
                    url=feed_url,
                    enabled=True,
                    fetch_interval=settings.rss_poll_interval
                )
                db.add(source)
                logger.info(f"Added RSS source: {name}")

        db.commit()
