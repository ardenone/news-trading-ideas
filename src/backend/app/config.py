"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/news_trading.db"

    # OpenAI API
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_CLUSTERING_MODEL: str = "gpt-5-mini"  # For grouping headlines
    OPENAI_IDEAS_MODEL: str = "gpt-5"  # For trading ideas with thinking
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    ENABLE_WEB_SEARCH: bool = True  # Enable web search for trading ideas

    # Application
    APP_NAME: str = "News Trading Ideas"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # RSS Feed Polling
    FEED_POLL_INTERVAL: int = 300  # seconds (5 minutes)
    RSS_TIMEOUT: int = 10  # seconds
    RSS_MAX_RETRIES: int = 3

    # AI Processing
    AI_PROCESS_INTERVAL: int = 600  # seconds (10 minutes)
    CLUSTERING_BATCH_SIZE: int = 40  # articles per batch
    CLUSTERING_THRESHOLD: float = 0.8  # cosine similarity threshold
    TOP_EVENTS_FOR_IDEAS: int = 10  # generate ideas for top N events

    # API Rate Limits
    MAX_DAILY_OPENAI_COST: float = 5.0  # dollars
    OPENAI_REQUESTS_PER_MINUTE: int = 50

    # Data Retention
    DATA_RETENTION_DAYS: int = 24  # keep articles for 24 hours
    EVENT_STALE_THRESHOLD_HOURS: int = 6

    # Performance
    MAX_WORKERS: int = 3  # concurrent API calls
    CACHE_TTL: int = 3600  # seconds (1 hour)

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
