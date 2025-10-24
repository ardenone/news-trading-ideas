"""Background task scheduler for RSS ingestion."""

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import logging

from database import SessionLocal
from services.rss_service import RSSService
from config import settings

logger = logging.getLogger(__name__)


class RSSScheduler:
    """Scheduler for periodic RSS feed ingestion."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False

    def fetch_rss_job(self):
        """Job to fetch all RSS feeds."""
        logger.info("Starting scheduled RSS fetch")
        db = SessionLocal()
        try:
            results = RSSService.fetch_all_sources(db)
            total_new = sum(r.get("new_articles", 0) for r in results)
            logger.info(f"RSS fetch complete: {total_new} new articles")
        except Exception as e:
            logger.error(f"Error in RSS fetch job: {e}")
        finally:
            db.close()

    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        # Add RSS fetch job
        self.scheduler.add_job(
            self.fetch_rss_job,
            "interval",
            seconds=settings.rss_poll_interval,
            id="rss_fetch",
            replace_existing=True
        )

        # Run immediately on startup
        self.scheduler.add_job(
            self.fetch_rss_job,
            "date",
            run_date=None,  # Run immediately
            id="rss_fetch_startup"
        )

        self.scheduler.start()
        self.running = True
        logger.info(f"RSS scheduler started (interval: {settings.rss_poll_interval}s)")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("RSS scheduler stopped")


# Global scheduler instance
rss_scheduler = RSSScheduler()
