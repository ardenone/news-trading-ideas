"""Main FastAPI application for News Trading Ideas MVP."""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime
import time

from config import settings
from database import get_db, init_db, NewsArticle, NewsCluster, TradingIdea, RSSSource
from models import (
    NewsArticleResponse, NewsArticleList,
    NewsClusterResponse, NewsClusterList,
    TradingIdeaResponse, TradingIdeaList,
    HealthResponse, GenerateClustersRequest, GenerateIdeasRequest
)
from services.rss_service import RSSService
from services.cluster_service import ClusterService
from services.ideas_service import IdeasService
from services.openai_service import OpenAIService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application startup time
START_TIME = time.time()

# Create FastAPI app
app = FastAPI(
    title="News Trading Ideas API",
    description="AI-powered news clustering and trading ideas generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and RSS sources on startup."""
    logger.info("Starting News Trading Ideas API")
    init_db()

    # Initialize RSS sources from config
    db = next(get_db())
    try:
        RSSService.initialize_sources(db)
    finally:
        db.close()

    logger.info("Startup complete")


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Check database
    db_healthy = True
    try:
        db.execute("SELECT 1")
    except Exception:
        db_healthy = False

    # Check OpenAI
    openai_healthy = await OpenAIService.test_connection()

    # Get last RSS fetch
    last_fetch = None
    latest_source = db.query(RSSSource).order_by(RSSSource.last_fetch.desc()).first()
    if latest_source and latest_source.last_fetch:
        last_fetch = latest_source.last_fetch

    # Determine overall status
    if db_healthy and openai_healthy:
        status = "healthy"
    elif db_healthy or openai_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        database=db_healthy,
        openai=openai_healthy,
        uptime=int(time.time() - START_TIME),
        last_rss_fetch=last_fetch
    )


# News endpoints
@app.get(f"{settings.api_prefix}/news", response_model=NewsArticleList)
async def list_news(
    skip: int = 0,
    limit: int = 50,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List news articles."""
    query = db.query(NewsArticle).order_by(NewsArticle.fetched_at.desc())

    if source:
        query = query.filter(NewsArticle.source == source)

    total = query.count()
    articles = query.offset(skip).limit(limit).all()

    return NewsArticleList(
        articles=articles,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@app.get(f"{settings.api_prefix}/news/{{article_id}}", response_model=NewsArticleResponse)
async def get_news(article_id: int, db: Session = Depends(get_db)):
    """Get specific news article."""
    article = db.query(NewsArticle).filter_by(id=article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.post(f"{settings.api_prefix}/news/refresh")
async def refresh_news(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger RSS feed refresh."""
    def refresh_task():
        db_session = next(get_db())
        try:
            results = RSSService.fetch_all_sources(db_session)
            logger.info(f"RSS refresh complete: {results}")
        finally:
            db_session.close()

    background_tasks.add_task(refresh_task)
    return {"message": "RSS refresh initiated", "status": "processing"}


# Cluster endpoints
@app.get(f"{settings.api_prefix}/clusters", response_model=NewsClusterList)
async def list_clusters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List news clusters."""
    clusters = ClusterService.list_clusters(db, skip=skip, limit=limit)
    total = db.query(NewsCluster).count()

    return NewsClusterList(clusters=clusters, total=total)


@app.get(f"{settings.api_prefix}/clusters/{{cluster_id}}", response_model=NewsClusterResponse)
async def get_cluster(cluster_id: int, db: Session = Depends(get_db)):
    """Get specific cluster with articles."""
    cluster = ClusterService.get_cluster_with_articles(db, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@app.post(f"{settings.api_prefix}/clusters/generate")
async def generate_clusters(
    request: GenerateClustersRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate news clusters from unclustered articles."""
    async def cluster_task():
        db_session = next(get_db())
        try:
            result = await ClusterService.cluster_articles(
                db_session,
                min_articles=request.min_articles,
                force=request.force
            )
            logger.info(f"Clustering complete: {result}")
        finally:
            db_session.close()

    background_tasks.add_task(cluster_task)
    return {"message": "Clustering initiated", "status": "processing"}


# Trading Ideas endpoints
@app.get(f"{settings.api_prefix}/ideas", response_model=TradingIdeaList)
async def list_ideas(
    skip: int = 0,
    limit: int = 100,
    min_confidence: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List trading ideas."""
    ideas = IdeasService.list_ideas(db, skip=skip, limit=limit, min_confidence=min_confidence)
    total = db.query(TradingIdea).count()

    return TradingIdeaList(ideas=ideas, total=total)


@app.get(f"{settings.api_prefix}/ideas/{{idea_id}}", response_model=TradingIdeaResponse)
async def get_idea(idea_id: int, db: Session = Depends(get_db)):
    """Get specific trading idea."""
    idea = IdeasService.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Trading idea not found")
    return idea


@app.post(f"{settings.api_prefix}/ideas/generate")
async def generate_ideas(
    request: GenerateIdeasRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate trading ideas from clusters."""
    async def ideas_task():
        db_session = next(get_db())
        try:
            result = await IdeasService.generate_ideas(
                db_session,
                cluster_ids=request.cluster_ids,
                force=request.force
            )
            logger.info(f"Ideas generation complete: {result}")
        finally:
            db_session.close()

    background_tasks.add_task(ideas_task)
    return {"message": "Ideas generation initiated", "status": "processing"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers
    )
