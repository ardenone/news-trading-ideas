"""Configuration management for News Trading Ideas MVP."""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-ada-002"
    completion_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 1000
    temperature: float = 0.7

    # Application Settings
    app_env: str = "production"
    log_level: str = "info"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./news.db"

    # RSS Configuration
    rss_poll_interval: int = 300  # seconds
    rss_feeds: str = ""  # Comma-separated URLs

    # API Settings
    cors_origins: str = "http://localhost:8000"
    api_prefix: str = "/api"

    # Clustering Parameters
    clustering_algorithm: str = "dbscan"
    clustering_eps: float = 0.3
    clustering_min_samples: int = 2

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Server Configuration
    backend_port: int = 8001
    frontend_port: int = 8000
    workers: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def rss_feed_list(self) -> List[str]:
        """Parse RSS feeds from comma-separated string."""
        if not self.rss_feeds:
            return []
        return [feed.strip() for feed in self.rss_feeds.split(",") if feed.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
