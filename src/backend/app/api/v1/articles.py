"""Article endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Article
from app.schemas.article import ArticleResponse, ArticleListResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    source: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List articles with optional filtering"""
    query = select(Article)

    if source:
        query = query.where(Article.source == source)
    if status:
        query = query.where(Article.processed_status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get articles
    query = query.order_by(desc(Article.publish_datetime)).offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListResponse(
        articles=articles,
        total=total,
        offset=skip,
        limit=limit,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific article"""
    result = await db.execute(
        select(Article).where(Article.article_id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
