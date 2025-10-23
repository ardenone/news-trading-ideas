"""Trading idea schemas"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class TradingIdeaResponse(BaseModel):
    idea_id: int
    event_id: int
    headline: str
    summary: str
    trading_thesis: str
    confidence_score: float
    generated_at: datetime
    status: str
    expires_at: Optional[datetime] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    research_highlights: Optional[list[str]] = None
    risk_warnings: Optional[list[str]] = None

    class Config:
        from_attributes = True


class IdeaListResponse(BaseModel):
    ideas: list[TradingIdeaResponse]
    total: int
    offset: int
    limit: int
