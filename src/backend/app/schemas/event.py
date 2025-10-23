"""Event schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.article import ArticleResponse


class NewsEventResponse(BaseModel):
    event_id: int
    event_summary: str
    event_key: Optional[str] = None
    first_reported_time: datetime
    last_updated: datetime
    source_count: int
    article_count: int
    relevance_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class NewsEventDetailResponse(NewsEventResponse):
    articles: list[ArticleResponse] = []


class EventListResponse(BaseModel):
    events: list[NewsEventResponse]
    total: int
    offset: int
    limit: int
