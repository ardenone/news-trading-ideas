"""Article schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArticleResponse(BaseModel):
    article_id: int
    feed_id: int
    headline: str
    url: str
    source: str
    publish_datetime: datetime
    processed_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    offset: int
    limit: int
