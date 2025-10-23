"""RSS feed ingestion service"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
import feedparser
import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import RSSFeed, Article

logger = structlog.get_logger()


class RSSIngestionService:
    """Service for fetching and parsing RSS feeds"""

    def __init__(self):
        self.timeout = settings.RSS_TIMEOUT
        self.max_retries = settings.RSS_MAX_RETRIES
        self.user_agent = "NewsTrading/1.0 (compatible; trading system)"

    async def fetch_feed(self, feed: RSSFeed, session: AsyncSession) -> int:
        """
        Fetch and process a single RSS feed

        Args:
            feed: RSS feed configuration
            session: Database session

        Returns:
            Number of new articles ingested
        """
        logger.info("fetching_feed", feed_id=feed.feed_id, source=feed.source_name)

        try:
            # Fetch feed content
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(feed.feed_url, headers=headers)
                response.raise_for_status()

            # Parse RSS/Atom
            parsed = feedparser.parse(response.content)

            if parsed.bozo:
                logger.warning(
                    "feed_parse_warning",
                    feed_id=feed.feed_id,
                    error=parsed.bozo_exception,
                )

            # Process entries
            new_articles = 0
            for entry in parsed.entries:
                try:
                    article = await self._parse_entry(entry, feed)
                    if article and await self._is_new_article(article, session):
                        session.add(article)
                        new_articles += 1
                except Exception as e:
                    logger.error(
                        "entry_parse_error",
                        feed_id=feed.feed_id,
                        error=str(e),
                    )
                    continue

            # Update feed metadata
            feed.last_fetched = datetime.utcnow()
            feed.next_fetch_scheduled = datetime.utcnow() + timedelta(
                seconds=feed.update_interval
            )
            feed.error_count = 0
            feed.last_error = None

            await session.commit()

            logger.info(
                "feed_fetched_success",
                feed_id=feed.feed_id,
                new_articles=new_articles,
            )

            return new_articles

        except httpx.HTTPError as e:
            logger.error(
                "feed_fetch_http_error",
                feed_id=feed.feed_id,
                error=str(e),
            )
            feed.error_count += 1
            feed.last_error = str(e)
            await session.commit()
            raise

        except Exception as e:
            logger.error(
                "feed_fetch_error",
                feed_id=feed.feed_id,
                error=str(e),
            )
            feed.error_count += 1
            feed.last_error = str(e)
            await session.commit()
            raise

    async def _parse_entry(
        self, entry: dict, feed: RSSFeed
    ) -> Optional[Article]:
        """Parse RSS entry into Article model"""
        try:
            # Extract required fields
            url = entry.get("link")
            if not url:
                return None

            title = entry.get("title", "")
            if not title:
                return None

            # Parse publish date
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                publish_datetime = datetime(*published_parsed[:6])
            else:
                publish_datetime = datetime.utcnow()

            # Extract content
            raw_content = None
            if "content" in entry:
                raw_content = entry.content[0].value
            elif "summary" in entry:
                raw_content = entry.summary
            elif "description" in entry:
                raw_content = entry.description

            # Generate content hash for deduplication
            hash_input = f"{title}{url}".encode("utf-8")
            content_hash = hashlib.sha256(hash_input).hexdigest()

            article = Article(
                feed_id=feed.feed_id,
                headline=title,
                url=url,
                source=feed.source_name,
                publish_datetime=publish_datetime,
                processed_status="pending",
                content_hash=content_hash,
                raw_content=raw_content,
            )

            return article

        except Exception as e:
            logger.error("entry_parse_error", error=str(e), entry_id=entry.get("id"))
            return None

    async def _is_new_article(
        self, article: Article, session: AsyncSession
    ) -> bool:
        """Check if article is new (not duplicate)"""
        # Check by URL
        result = await session.execute(
            select(Article).where(Article.url == article.url)
        )
        if result.scalar_one_or_none():
            return False

        # Check by content hash
        if article.content_hash:
            result = await session.execute(
                select(Article).where(Article.content_hash == article.content_hash)
            )
            if result.scalar_one_or_none():
                return False

        return True

    async def fetch_all_feeds(self, session: AsyncSession) -> int:
        """
        Fetch all active feeds that are due for refresh

        Args:
            session: Database session

        Returns:
            Total number of new articles
        """
        # Get feeds due for refresh
        result = await session.execute(
            select(RSSFeed)
            .where(RSSFeed.is_active == True)
            .where(
                (RSSFeed.next_fetch_scheduled <= datetime.utcnow())
                | (RSSFeed.next_fetch_scheduled.is_(None))
            )
        )
        feeds = result.scalars().all()

        logger.info("fetching_all_feeds", feed_count=len(feeds))

        # Fetch feeds concurrently (max 5 at a time)
        total_new = 0
        for i in range(0, len(feeds), 5):
            batch = feeds[i : i + 5]
            results = await asyncio.gather(
                *[self.fetch_feed(feed, session) for feed in batch],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, int):
                    total_new += result
                elif isinstance(result, Exception):
                    logger.error("feed_batch_error", error=str(result))

        return total_new


# Global service instance
rss_service = RSSIngestionService()
