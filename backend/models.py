"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


# News Article models
class NewsArticleBase(BaseModel):
    """Base news article schema."""
    url: str
    title: str
    content: Optional[str] = None
    source: str
    published_at: Optional[datetime] = None


class NewsArticleCreate(NewsArticleBase):
    """Schema for creating a news article."""
    pass


class NewsArticleResponse(NewsArticleBase):
    """Schema for news article response."""
    id: int
    fetched_at: datetime
    cluster_id: Optional[int] = None

    class Config:
        from_attributes = True


class NewsArticleList(BaseModel):
    """Schema for listing news articles."""
    articles: List[NewsArticleResponse]
    total: int
    page: int = 1
    page_size: int = 50


# News Cluster models
class NewsClusterBase(BaseModel):
    """Base news cluster schema."""
    theme: str
    summary: Optional[str] = None
    confidence_score: Optional[float] = None


class NewsClusterCreate(NewsClusterBase):
    """Schema for creating a news cluster."""
    pass


class NewsClusterResponse(NewsClusterBase):
    """Schema for news cluster response."""
    id: int
    article_count: int
    created_at: datetime
    articles: List[NewsArticleResponse] = []

    class Config:
        from_attributes = True


class NewsClusterList(BaseModel):
    """Schema for listing news clusters."""
    clusters: List[NewsClusterResponse]
    total: int


# Trading Idea models
class TradingIdeaBase(BaseModel):
    """Base trading idea schema."""
    idea: str
    rationale: str
    instruments: List[str] = Field(default_factory=list)
    direction: str = Field(..., pattern="^(long|short|neutral)$")
    time_horizon: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

    @validator("direction")
    def validate_direction(cls, v):
        if v not in ["long", "short", "neutral"]:
            raise ValueError("direction must be 'long', 'short', or 'neutral'")
        return v


class TradingIdeaCreate(TradingIdeaBase):
    """Schema for creating a trading idea."""
    cluster_id: int


class TradingIdeaResponse(TradingIdeaBase):
    """Schema for trading idea response."""
    id: int
    cluster_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TradingIdeaList(BaseModel):
    """Schema for listing trading ideas."""
    ideas: List[TradingIdeaResponse]
    total: int


# RSS Source models
class RSSSourceBase(BaseModel):
    """Base RSS source schema."""
    name: str
    url: str
    enabled: bool = True
    fetch_interval: int = 300


class RSSSourceCreate(RSSSourceBase):
    """Schema for creating RSS source."""
    pass


class RSSSourceResponse(RSSSourceBase):
    """Schema for RSS source response."""
    id: int
    last_fetch: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Health check model
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    database: bool
    openai: bool
    uptime: int
    last_rss_fetch: Optional[datetime] = None
    version: str = "1.0.0"


# Generation request models
class GenerateClustersRequest(BaseModel):
    """Request to generate news clusters."""
    min_articles: int = Field(default=10, ge=2)
    force: bool = False  # Force regeneration even if articles are already clustered


class GenerateIdeasRequest(BaseModel):
    """Request to generate trading ideas."""
    cluster_ids: Optional[List[int]] = None  # If None, generate for all clusters
    force: bool = False  # Force regeneration
