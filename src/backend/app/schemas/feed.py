"""Feed schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class RSSFeedBase(BaseModel):
    feed_url: str
    source_name: str
    category: str = "general"
    update_interval: int = 300
    is_active: bool = True


class RSSFeedCreate(RSSFeedBase):
    pass


class RSSFeedResponse(RSSFeedBase):
    feed_id: int
    last_fetched: Optional[datetime] = None
    next_fetch_scheduled: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    error_count: int
    last_error: Optional[str] = None

    class Config:
        from_attributes = True
