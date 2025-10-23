"""News Event endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import NewsEvent, EventArticle, Article
from app.schemas.event import (
    NewsEventResponse,
    NewsEventDetailResponse,
    EventListResponse,
)
from app.schemas.article import ArticleResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventListResponse)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query("active"),
    sort: str = Query("relevance"),  # relevance or time
    db: AsyncSession = Depends(get_db),
):
    """List news events"""
    query = select(NewsEvent).where(NewsEvent.status == status)

    # Apply sorting
    if sort == "relevance":
        query = query.order_by(desc(NewsEvent.relevance_score))
    else:
        query = query.order_by(desc(NewsEvent.first_reported_time))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get events
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        events=events,
        total=total,
        offset=skip,
        limit=limit,
    )


@router.get("/{event_id}", response_model=NewsEventDetailResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get event details with articles"""
    # Get event
    result = await db.execute(
        select(NewsEvent).where(NewsEvent.event_id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get associated articles
    result = await db.execute(
        select(EventArticle).where(EventArticle.event_id == event_id)
    )
    mappings = result.scalars().all()

    articles = []
    for mapping in mappings:
        result = await db.execute(
            select(Article).where(Article.article_id == mapping.article_id)
        )
        article = result.scalar_one_or_none()
        if article:
            articles.append(article)

    # Sort by publish time
    articles.sort(key=lambda a: a.publish_datetime, reverse=True)

    return NewsEventDetailResponse(
        **event.__dict__,
        articles=articles,
    )
