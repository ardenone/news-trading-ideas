"""Trading Ideas endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import TradingIdea, NewsEvent
from app.schemas.idea import TradingIdeaResponse, IdeaListResponse

router = APIRouter(prefix="/ideas", tags=["trading_ideas"])


@router.get("/", response_model=IdeaListResponse)
async def list_ideas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    status: str = Query("new"),
    min_confidence: float = Query(0.0, ge=0.0, le=10.0),
    db: AsyncSession = Depends(get_db),
):
    """List trading ideas"""
    query = select(TradingIdea).where(TradingIdea.status == status).where(
        TradingIdea.confidence_score >= min_confidence
    )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get ideas
    query = query.order_by(desc(TradingIdea.generated_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    ideas = result.scalars().all()

    return IdeaListResponse(
        ideas=ideas,
        total=total,
        offset=skip,
        limit=limit,
    )


@router.get("/{idea_id}", response_model=TradingIdeaResponse)
async def get_idea(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific trading idea"""
    result = await db.execute(
        select(TradingIdea).where(TradingIdea.idea_id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Trading idea not found")
    return idea
