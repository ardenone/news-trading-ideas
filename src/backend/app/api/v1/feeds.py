"""RSS Feed endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import RSSFeed
from app.schemas.feed import RSSFeedCreate, RSSFeedResponse
from app.services.rss_ingestion import rss_service

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.get("/", response_model=List[RSSFeedResponse])
async def list_feeds(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all RSS feeds"""
    result = await db.execute(select(RSSFeed).offset(skip).limit(limit))
    feeds = result.scalars().all()
    return feeds


@router.post("/", response_model=RSSFeedResponse, status_code=201)
async def create_feed(
    feed: RSSFeedCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new RSS feed"""
    # Check if feed already exists
    result = await db.execute(
        select(RSSFeed).where(RSSFeed.feed_url == feed.feed_url)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Feed already exists")

    db_feed = RSSFeed(**feed.dict())
    db.add(db_feed)
    await db.commit()
    await db.refresh(db_feed)
    return db_feed


@router.get("/{feed_id}", response_model=RSSFeedResponse)
async def get_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific feed"""
    result = await db.execute(select(RSSFeed).where(RSSFeed.feed_id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


@router.post("/{feed_id}/refresh")
async def refresh_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger feed refresh"""
    result = await db.execute(select(RSSFeed).where(RSSFeed.feed_id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    try:
        new_articles = await rss_service.fetch_feed(feed, db)
        return {"status": "success", "new_articles": new_articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a feed"""
    result = await db.execute(select(RSSFeed).where(RSSFeed.feed_id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    await db.delete(feed)
    await db.commit()
    return {"status": "deleted"}
