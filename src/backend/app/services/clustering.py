"""Event clustering service using OpenAI embeddings and GPT-5-mini for headline grouping"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import Article, NewsEvent, EventArticle
from app.core.openai_client import openai_client

logger = structlog.get_logger()


class ClusteringService:
    """Service for clustering articles into events using AI"""

    def __init__(self):
        self.batch_size = settings.CLUSTERING_BATCH_SIZE
        self.threshold = settings.CLUSTERING_THRESHOLD
        self.model = settings.OPENAI_CLUSTERING_MODEL

    async def cluster_pending_articles(self, session: AsyncSession) -> int:
        """
        Cluster all pending articles into events

        Args:
            session: Database session

        Returns:
            Number of events created/updated
        """
        # Fetch pending articles
        result = await session.execute(
            select(Article)
            .where(Article.processed_status == "pending")
            .order_by(Article.publish_datetime.desc())
            .limit(100)
        )
        articles = list(result.scalars().all())

        if not articles:
            logger.info("no_pending_articles")
            return 0

        logger.info("clustering_articles", count=len(articles))

        # Process in batches
        events_created = 0
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i : i + self.batch_size]
            try:
                events = await self._cluster_batch(batch, session)
                events_created += len(events)
            except Exception as e:
                logger.error("clustering_batch_error", error=str(e))
                # Mark articles as failed
                for article in batch:
                    article.processed_status = "failed"
                continue

        await session.commit()
        return events_created

    async def _cluster_batch(
        self, articles: List[Article], session: AsyncSession
    ) -> List[NewsEvent]:
        """Cluster a batch of articles using GPT-5-mini for efficient headline grouping"""

        # Build prompt
        headlines_json = []
        for article in articles:
            headlines_json.append(
                {
                    "id": article.article_id,
                    "source": article.source,
                    "title": article.headline,
                    "published_at": article.publish_datetime.isoformat(),
                    "url": article.url,
                }
            )

        prompt = f"""Analyze the following {len(articles)} financial news headlines and group them into distinct market events.

Headlines:
{json.dumps(headlines_json, indent=2)}

For each event cluster, provide:
1. event_summary: 2-3 sentence description of the event
2. event_key: Short normalized key for grouping (e.g., "aapl-q4-earnings")
3. headline_ids: Array of headline IDs belonging to this cluster
4. relevance_score: 1-10 scale (how market-moving is this event?)
5. first_reported: ISO timestamp of earliest headline

Output Format (JSON only):
{{
  "events": [
    {{
      "event_summary": "Apple reports Q4 earnings...",
      "event_key": "aapl-q4-earnings-2025",
      "headline_ids": [123, 456, 789],
      "relevance_score": 8,
      "first_reported": "2025-10-22T14:30:00Z"
    }}
  ],
  "ungrouped_headlines": [111, 222]
}}

Return only valid JSON. No markdown, no explanations."""

        # Call GPT-5-mini via Responses API for fast headline grouping
        response = await openai_client.create_response(
            input_text=prompt,
            model=self.model,  # gpt-5-mini
            instructions="You are an expert financial news analyst specializing in identifying market-moving events. Output must be valid JSON only.",
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        # Parse response
        try:
            clusters = json.loads(response["text"])
        except json.JSONDecodeError as e:
            logger.error("invalid_json_response", error=str(e), text=response["text"])
            raise

        # Create/update events
        created_events = []
        for cluster_data in clusters.get("events", []):
            event = await self._create_or_update_event(cluster_data, articles, session)
            created_events.append(event)

        # Mark ungrouped articles as processed
        ungrouped_ids = set(clusters.get("ungrouped_headlines", []))
        for article in articles:
            if article.article_id in ungrouped_ids:
                article.processed_status = "processed"

        logger.info(
            "clustering_complete",
            events_created=len(created_events),
            articles_grouped=len(articles) - len(ungrouped_ids),
        )

        return created_events

    async def _create_or_update_event(
        self, cluster_data: Dict[str, Any], articles: List[Article], session: AsyncSession
    ) -> NewsEvent:
        """Create new event or update existing one"""

        event_key = cluster_data.get("event_key")
        headline_ids = cluster_data.get("headline_ids", [])

        # Check if event exists
        result = await session.execute(
            select(NewsEvent).where(NewsEvent.event_key == event_key)
        )
        event = result.scalar_one_or_none()

        # Get first reported time
        first_reported_str = cluster_data.get("first_reported")
        try:
            first_reported = datetime.fromisoformat(
                first_reported_str.replace("Z", "+00:00")
            )
        except:
            first_reported = datetime.utcnow()

        if not event:
            # Create new event
            event = NewsEvent(
                event_summary=cluster_data.get("event_summary"),
                event_key=event_key,
                first_reported_time=first_reported,
                last_updated=datetime.utcnow(),
                relevance_score=cluster_data.get("relevance_score", 0.0),
                status="active",
            )
            session.add(event)
            await session.flush()  # Get event_id

            logger.info("event_created", event_id=event.event_id, event_key=event_key)
        else:
            # Update existing event
            event.event_summary = cluster_data.get("event_summary")
            event.last_updated = datetime.utcnow()
            event.relevance_score = max(
                event.relevance_score, cluster_data.get("relevance_score", 0.0)
            )

            logger.info("event_updated", event_id=event.event_id, event_key=event_key)

        # Link articles to event
        article_map = {a.article_id: a for a in articles}
        for article_id in headline_ids:
            article = article_map.get(article_id)
            if article:
                # Check if mapping exists
                result = await session.execute(
                    select(EventArticle)
                    .where(EventArticle.event_id == event.event_id)
                    .where(EventArticle.article_id == article_id)
                )
                if not result.scalar_one_or_none():
                    mapping = EventArticle(
                        event_id=event.event_id,
                        article_id=article_id,
                        contribution_score=1.0,
                    )
                    session.add(mapping)

                # Mark article as processed
                article.processed_status = "processed"
                article.processed_at = datetime.utcnow()

        # Update source count
        result = await session.execute(
            select(EventArticle).where(EventArticle.event_id == event.event_id)
        )
        mappings = result.scalars().all()
        event.article_count = len(mappings)

        # Count unique sources
        sources = set()
        for mapping in mappings:
            result = await session.execute(
                select(Article).where(Article.article_id == mapping.article_id)
            )
            article = result.scalar_one_or_none()
            if article:
                sources.add(article.source)
        event.source_count = len(sources)

        return event

    async def mark_stale_events(self, session: AsyncSession):
        """Mark events as stale if no updates in threshold hours"""
        threshold_time = datetime.utcnow() - timedelta(
            hours=settings.EVENT_STALE_THRESHOLD_HOURS
        )

        result = await session.execute(
            select(NewsEvent)
            .where(NewsEvent.status == "active")
            .where(NewsEvent.last_updated < threshold_time)
        )
        events = result.scalars().all()

        for event in events:
            event.status = "stale"
            logger.info("event_marked_stale", event_id=event.event_id)

        await session.commit()


# Global service instance
clustering_service = ClusteringService()
