#!/usr/bin/env python
"""Seed database with priority RSS feeds from MVP list"""

import asyncio
from app.database import AsyncSessionLocal
from app.models import RSSFeed

# Priority feeds from PRIORITY-FEEDS-FOR-MVP.md
PRIORITY_FEEDS = [
    # Markets & Finance
    {
        "feed_url": "https://www.cnbc.com/id/15838459/device/rss/rss.html",
        "source_name": "CNBC Markets",
        "category": "finance",
        "update_interval": 300,
    },
    {
        "feed_url": "https://finance.yahoo.com/news/rssindex",
        "source_name": "Yahoo Finance",
        "category": "finance",
        "update_interval": 300,
    },
    {
        "feed_url": "https://seekingalpha.com/feed.xml",
        "source_name": "Seeking Alpha",
        "category": "finance",
        "update_interval": 3600,
    },
    # Politics & Policy
    {
        "feed_url": "https://thehill.com/homenews/feed/",
        "source_name": "The Hill - All News",
        "category": "politics",
        "update_interval": 3600,
    },
    {
        "feed_url": "https://feeds.washingtonpost.com/rss/politics",
        "source_name": "Washington Post Politics",
        "category": "politics",
        "update_interval": 3600,
    },
    # General News
    {
        "feed_url": "https://feeds.nbcnews.com/nbcnews/public/news",
        "source_name": "NBC News",
        "category": "general",
        "update_interval": 300,
    },
    {
        "feed_url": "https://www.cbsnews.com/latest/rss/main",
        "source_name": "CBS News",
        "category": "general",
        "update_interval": 300,
    },
    {
        "feed_url": "https://techcrunch.com/feed",
        "source_name": "TechCrunch",
        "category": "tech",
        "update_interval": 300,
    },
]


async def seed_feeds():
    """Seed database with priority feeds"""
    async with AsyncSessionLocal() as session:
        for feed_data in PRIORITY_FEEDS:
            # Check if feed exists
            feed = RSSFeed(**feed_data, is_active=True)
            session.add(feed)
            print(f"Added: {feed_data['source_name']}")

        await session.commit()
        print(f"\nSeeded {len(PRIORITY_FEEDS)} RSS feeds")


if __name__ == "__main__":
    asyncio.run(seed_feeds())
