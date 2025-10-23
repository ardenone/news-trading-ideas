"""FastAPI main application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from app.config import settings
from app.database import init_db
from app.api.v1 import feeds, articles, events, ideas
from app.workers.scheduler import scheduler

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("application_startup", version=settings.VERSION)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    # Start background scheduler
    scheduler.start()
    logger.info("scheduler_started")

    yield

    # Shutdown
    logger.info("application_shutdown")
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS middleware
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(feeds.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(ideas.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }
