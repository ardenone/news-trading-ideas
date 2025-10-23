"""Trading ideas generation service using OpenAI GPT-4"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import NewsEvent, TradingIdea, EventArticle, Article
from app.core.openai_client import openai_client

logger = structlog.get_logger()


class IdeaGenerationService:
    """Service for generating trading ideas from news events"""

    def __init__(self):
        self.model = settings.OPENAI_IDEAS_MODEL
        self.top_n = settings.TOP_EVENTS_FOR_IDEAS

    async def generate_ideas_for_top_events(self, session: AsyncSession) -> int:
        """
        Generate trading ideas for top-ranked events

        Args:
            session: Database session

        Returns:
            Number of trading ideas generated
        """
        # Get top active events without ideas
        result = await session.execute(
            select(NewsEvent)
            .where(NewsEvent.status == "active")
            .outerjoin(TradingIdea)
            .where(TradingIdea.idea_id.is_(None))
            .order_by(desc(NewsEvent.relevance_score))
            .limit(self.top_n)
        )
        events = list(result.scalars().all())

        if not events:
            logger.info("no_events_for_ideas")
            return 0

        logger.info("generating_ideas", event_count=len(events))

        # Generate ideas for each event
        ideas_generated = 0
        for event in events:
            try:
                idea = await self.generate_idea(event, session)
                if idea:
                    ideas_generated += 1
            except Exception as e:
                logger.error(
                    "idea_generation_error",
                    event_id=event.event_id,
                    error=str(e),
                )
                continue

        await session.commit()
        return ideas_generated

    async def generate_idea(
        self, event: NewsEvent, session: AsyncSession
    ) -> Optional[TradingIdea]:
        """
        Generate a trading idea for a single event

        Args:
            event: News event
            session: Database session

        Returns:
            Generated trading idea or None if no viable idea
        """
        logger.info("generating_idea_for_event", event_id=event.event_id)

        # Gather event context
        context = await self._gather_event_context(event, session)

        # Build prompt
        prompt = await self._build_prompt(event, context)

        # Call GPT-4 via Responses API
        try:
            response = await openai_client.create_response(
                input_text=prompt,
                model=self.model,
                instructions="You are an expert trading strategist. Generate actionable trading ideas based on news events. Output must be valid JSON only. If no viable trade idea exists, return {\"no_trade\": true, \"reason\": \"...\"}.",
                temperature=0.7,
                max_output_tokens=2000,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.error("openai_api_error", event_id=event.event_id, error=str(e))
            raise

        # Parse response
        try:
            idea_data = json.loads(response["text"])
        except json.JSONDecodeError as e:
            logger.error(
                "invalid_json_response",
                event_id=event.event_id,
                error=str(e),
                text=response["text"],
            )
            raise

        # Check if no trade scenario
        if idea_data.get("no_trade"):
            logger.info(
                "no_viable_trade",
                event_id=event.event_id,
                reason=idea_data.get("reason"),
            )
            return None

        # Create trading idea
        idea = TradingIdea(
            event_id=event.event_id,
            headline=idea_data.get("headline", event.event_summary[:200]),
            summary=idea_data.get("summary", ""),
            trading_thesis=idea_data.get("trading_thesis", ""),
            confidence_score=idea_data.get("confidence_score", 0.0),
            status="new",
            expires_at=datetime.utcnow() + timedelta(days=3),
            model_used=self.model,
            tokens_used=response["usage"]["total_tokens"],
            cost_usd=response["cost"],
            research_highlights=idea_data.get("research_highlights", []),
            risk_warnings=idea_data.get("risk_warnings", []),
        )

        session.add(idea)
        await session.flush()  # Get idea_id

        logger.info(
            "trading_idea_created",
            idea_id=idea.idea_id,
            event_id=event.event_id,
            confidence=idea.confidence_score,
            cost=response["cost"],
        )

        return idea

    async def _gather_event_context(
        self, event: NewsEvent, session: AsyncSession
    ) -> Dict[str, Any]:
        """Gather contextual information about the event"""

        # Get all articles for this event
        result = await session.execute(
            select(EventArticle).where(EventArticle.event_id == event.event_id)
        )
        mappings = list(result.scalars().all())

        articles = []
        for mapping in mappings:
            result = await session.execute(
                select(Article).where(Article.article_id == mapping.article_id)
            )
            article = result.scalar_one_or_none()
            if article:
                articles.append(article)

        # Sort by publish time
        articles.sort(key=lambda a: a.publish_datetime)

        # Build context
        context = {
            "article_count": len(articles),
            "source_count": event.source_count,
            "first_reported": event.first_reported_time.isoformat(),
            "latest_update": event.last_updated.isoformat(),
            "articles": [
                {
                    "source": a.source,
                    "headline": a.headline,
                    "published": a.publish_datetime.isoformat(),
                }
                for a in articles[:10]  # Top 10 articles
            ],
        }

        return context

    async def _build_prompt(
        self, event: NewsEvent, context: Dict[str, Any]
    ) -> str:
        """Build prompt for trading idea generation"""

        prompt = f"""Analyze the following market event and generate a trading idea.

Event Summary:
{event.event_summary}

Event Context:
- Articles: {context['article_count']} from {context['source_count']} sources
- First reported: {context['first_reported']}
- Latest update: {context['latest_update']}
- Relevance score: {event.relevance_score}/10

Sample Headlines:
{json.dumps(context['articles'], indent=2)}

Your Task:
Generate a structured trading idea based on this event. If the event is not actionable or lacks sufficient market impact, return {{"no_trade": true, "reason": "explanation"}}.

Otherwise, provide:
{{
  "headline": "Concise trading idea headline",
  "summary": "2-3 sentence executive summary",
  "trading_thesis": "Detailed analysis of why this event creates a trading opportunity",
  "confidence_score": 7.5,  // 0-10 scale
  "research_highlights": [
    "Key insight 1",
    "Key insight 2",
    "Key insight 3"
  ],
  "risk_warnings": [
    "Risk factor 1",
    "Risk factor 2"
  ]
}}

Guidelines:
- Focus on actionable, high-probability trades
- Consider timeframe (intraday, swing, position)
- Assess market impact realistically
- If confidence < 6.0, return no_trade instead
- Be conservative with speculation

Return only valid JSON."""

        return prompt


# Global service instance
idea_service = IdeaGenerationService()
