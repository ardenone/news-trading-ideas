"""APScheduler background jobs"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import structlog
from app.config import settings
from app.database import AsyncSessionLocal
from app.services.rss_ingestion import rss_service
from app.services.clustering import clustering_service
from app.services.idea_generation import idea_service

logger = structlog.get_logger()

# Create scheduler
scheduler = AsyncIOScheduler()


async def fetch_rss_feeds_job():
    """Periodic job to fetch RSS feeds"""
    logger.info("rss_fetch_job_started")

    async with AsyncSessionLocal() as session:
        try:
            new_articles = await rss_service.fetch_all_feeds(session)
            logger.info("rss_fetch_job_completed", new_articles=new_articles)
        except Exception as e:
            logger.error("rss_fetch_job_error", error=str(e))


async def cluster_articles_job():
    """Periodic job to cluster articles into events"""
    logger.info("clustering_job_started")

    async with AsyncSessionLocal() as session:
        try:
            events_created = await clustering_service.cluster_pending_articles(session)
            logger.info("clustering_job_completed", events_created=events_created)

            # Mark stale events
            await clustering_service.mark_stale_events(session)
        except Exception as e:
            logger.error("clustering_job_error", error=str(e))


async def generate_ideas_job():
    """Periodic job to generate trading ideas"""
    logger.info("idea_generation_job_started")

    async with AsyncSessionLocal() as session:
        try:
            ideas_generated = await idea_service.generate_ideas_for_top_events(session)
            logger.info("idea_generation_job_completed", ideas_generated=ideas_generated)
        except Exception as e:
            logger.error("idea_generation_job_error", error=str(e))


# Schedule jobs
scheduler.add_job(
    fetch_rss_feeds_job,
    trigger=IntervalTrigger(seconds=settings.FEED_POLL_INTERVAL),
    id="fetch_rss_feeds",
    name="Fetch RSS Feeds",
    replace_existing=True,
    max_instances=1,
)

scheduler.add_job(
    cluster_articles_job,
    trigger=IntervalTrigger(seconds=settings.AI_PROCESS_INTERVAL),
    id="cluster_articles",
    name="Cluster Articles",
    replace_existing=True,
    max_instances=1,
)

scheduler.add_job(
    generate_ideas_job,
    trigger=IntervalTrigger(seconds=settings.AI_PROCESS_INTERVAL),
    id="generate_ideas",
    name="Generate Trading Ideas",
    replace_existing=True,
    max_instances=1,
)

logger.info(
    "scheduler_configured",
    jobs=[
        "fetch_rss_feeds",
        "cluster_articles",
        "generate_ideas",
    ],
)
