"""Trading ideas generation service."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from database import TradingIdea, NewsCluster
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class IdeasService:
    """Service for generating trading ideas from news clusters."""

    @staticmethod
    async def generate_ideas(
        db: Session,
        cluster_ids: Optional[List[int]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Generate trading ideas from clusters."""
        try:
            # Get clusters
            query = db.query(NewsCluster)

            if cluster_ids:
                query = query.filter(NewsCluster.id.in_(cluster_ids))

            clusters = query.all()

            if not clusters:
                return {
                    "success": False,
                    "message": "No clusters found",
                    "ideas_generated": 0
                }

            logger.info(f"Generating ideas for {len(clusters)} clusters")

            generated_ideas = []
            no_idea_count = 0
            error_count = 0

            for cluster in clusters:
                # Skip if cluster already has ideas and not forcing
                if not force and len(cluster.trading_ideas) > 0:
                    logger.debug(f"Cluster {cluster.id} already has ideas, skipping")
                    continue

                # Check if cluster has enough articles
                if cluster.article_count < 2:
                    logger.debug(f"Cluster {cluster.id} has too few articles ({cluster.article_count})")
                    continue

                # Prepare article data
                titles = [a.title for a in cluster.articles]
                summaries = [a.content[:200] if a.content else "" for a in cluster.articles]

                # Generate trading idea
                try:
                    idea_data = await OpenAIService.generate_trading_idea(
                        cluster.theme,
                        titles,
                        summaries
                    )

                    if idea_data is None:
                        no_idea_count += 1
                        logger.info(f"No viable idea for cluster {cluster.id}: {cluster.theme}")
                        continue

                    # Create trading idea
                    trading_idea = TradingIdea(
                        cluster_id=cluster.id,
                        idea=idea_data["idea"],
                        rationale=idea_data["rationale"],
                        instruments=idea_data["instruments"],
                        direction=idea_data["direction"],
                        time_horizon=idea_data.get("time_horizon", "medium"),
                        confidence=idea_data["confidence"]
                    )
                    db.add(trading_idea)
                    generated_ideas.append(trading_idea)

                    logger.info(
                        f"Generated idea for cluster {cluster.id}: "
                        f"{idea_data['direction']} {', '.join(idea_data['instruments'][:3])}"
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error generating idea for cluster {cluster.id}: {e}")
                    continue

            db.commit()

            return {
                "success": True,
                "clusters_processed": len(clusters),
                "ideas_generated": len(generated_ideas),
                "no_idea_count": no_idea_count,
                "errors": error_count,
                "ideas": [
                    {
                        "id": idea.id,
                        "cluster_id": idea.cluster_id,
                        "idea": idea.idea,
                        "direction": idea.direction,
                        "instruments": idea.instruments,
                        "confidence": idea.confidence
                    }
                    for idea in generated_ideas
                ]
            }

        except Exception as e:
            logger.error(f"Error in ideas generation: {e}")
            db.rollback()
            raise

    @staticmethod
    def get_idea(db: Session, idea_id: int) -> Optional[TradingIdea]:
        """Get trading idea by ID."""
        return db.query(TradingIdea).filter_by(id=idea_id).first()

    @staticmethod
    def list_ideas(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        min_confidence: Optional[float] = None
    ) -> List[TradingIdea]:
        """List trading ideas."""
        query = db.query(TradingIdea).order_by(TradingIdea.created_at.desc())

        if min_confidence is not None:
            query = query.filter(TradingIdea.confidence >= min_confidence)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_ideas_by_cluster(db: Session, cluster_id: int) -> List[TradingIdea]:
        """Get all trading ideas for a specific cluster."""
        return db.query(TradingIdea).filter_by(cluster_id=cluster_id).all()
