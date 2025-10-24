"""News clustering service using OpenAI embeddings."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np
from sklearn.cluster import DBSCAN
import logging

from database import NewsArticle, NewsCluster
from services.openai_service import OpenAIService
from config import settings

logger = logging.getLogger(__name__)


class ClusterService:
    """Service for clustering news articles."""

    @staticmethod
    async def cluster_articles(
        db: Session,
        min_articles: int = 10,
        force: bool = False
    ) -> Dict[str, Any]:
        """Cluster unclustered news articles."""
        try:
            # Get unclustered articles
            query = db.query(NewsArticle)
            if not force:
                query = query.filter(NewsArticle.cluster_id.is_(None))

            articles = query.all()

            if len(articles) < min_articles:
                logger.info(f"Not enough articles to cluster: {len(articles)} < {min_articles}")
                return {
                    "success": False,
                    "message": f"Need at least {min_articles} articles to cluster",
                    "article_count": len(articles)
                }

            logger.info(f"Clustering {len(articles)} articles")

            # Generate embeddings for articles that don't have them
            articles_needing_embeddings = [a for a in articles if not a.embedding]

            if articles_needing_embeddings:
                texts = [
                    f"{a.title} {a.content[:500] if a.content else ''}"
                    for a in articles_needing_embeddings
                ]

                embeddings = await OpenAIService.generate_embeddings_batch(texts)

                for article, embedding in zip(articles_needing_embeddings, embeddings):
                    article.embedding = embedding

                db.commit()
                logger.info(f"Generated embeddings for {len(articles_needing_embeddings)} articles")

            # Prepare embeddings matrix
            embeddings_matrix = np.array([a.embedding for a in articles])

            # Perform clustering
            clustering = DBSCAN(
                eps=settings.clustering_eps,
                min_samples=settings.clustering_min_samples,
                metric="cosine"
            )
            labels = clustering.fit_predict(embeddings_matrix)

            # Group articles by cluster
            clusters_dict = {}
            noise_count = 0

            for idx, label in enumerate(labels):
                if label == -1:  # Noise/outliers
                    noise_count += 1
                    continue

                if label not in clusters_dict:
                    clusters_dict[label] = []

                clusters_dict[label].append(articles[idx])

            logger.info(
                f"Clustering complete: {len(clusters_dict)} clusters, "
                f"{noise_count} outliers"
            )

            # Create cluster records and extract themes
            created_clusters = []
            for cluster_articles in clusters_dict.values():
                if len(cluster_articles) < settings.clustering_min_samples:
                    continue

                # Extract theme using OpenAI
                titles = [a.title for a in cluster_articles]
                theme_data = await OpenAIService.extract_cluster_theme(titles)

                # Create cluster
                cluster = NewsCluster(
                    theme=theme_data["theme"],
                    summary=theme_data["summary"],
                    article_count=len(cluster_articles),
                    confidence_score=theme_data["confidence"]
                )
                db.add(cluster)
                db.flush()  # Get cluster ID

                # Assign articles to cluster
                for article in cluster_articles:
                    article.cluster_id = cluster.id

                created_clusters.append(cluster)
                logger.info(f"Created cluster: {cluster.theme} ({len(cluster_articles)} articles)")

            db.commit()

            return {
                "success": True,
                "clusters_created": len(created_clusters),
                "articles_clustered": sum(c.article_count for c in created_clusters),
                "outliers": noise_count,
                "cluster_details": [
                    {
                        "id": c.id,
                        "theme": c.theme,
                        "article_count": c.article_count,
                        "confidence": c.confidence_score
                    }
                    for c in created_clusters
                ]
            }

        except Exception as e:
            logger.error(f"Error clustering articles: {e}")
            db.rollback()
            raise

    @staticmethod
    def get_cluster_with_articles(db: Session, cluster_id: int) -> Optional[NewsCluster]:
        """Get cluster with all associated articles."""
        return db.query(NewsCluster).filter_by(id=cluster_id).first()

    @staticmethod
    def list_clusters(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_articles: bool = True
    ) -> List[NewsCluster]:
        """List all clusters."""
        query = db.query(NewsCluster).order_by(NewsCluster.created_at.desc())
        return query.offset(skip).limit(limit).all()
