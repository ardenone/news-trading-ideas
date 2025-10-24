"""OpenAI integration service for embeddings and completions."""

from openai import OpenAI
from typing import List, Optional, Dict, Any
import numpy as np
from config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


class OpenAIService:
    """Service for OpenAI API interactions."""

    @staticmethod
    async def generate_embedding(text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    @staticmethod
    async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        try:
            # OpenAI supports batch embeddings
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    @staticmethod
    async def extract_cluster_theme(article_titles: List[str]) -> Dict[str, Any]:
        """Extract theme and summary from cluster of articles."""
        try:
            prompt = f"""Analyze these related news article titles and extract the main theme:

{chr(10).join(f"- {title}" for title in article_titles)}

Provide a response in the following format:
Theme: [A concise theme in 5-10 words]
Summary: [A 2-3 sentence summary of the overall narrative]
Confidence: [A number between 0 and 1 indicating how well these articles relate to each other]"""

            response = client.chat.completions.create(
                model=settings.completion_model,
                messages=[
                    {"role": "system", "content": "You are a financial news analyst expert at identifying themes and patterns in market news."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )

            content = response.choices[0].message.content

            # Parse response
            lines = content.strip().split("\n")
            theme = ""
            summary = ""
            confidence = 0.5

            for line in lines:
                if line.startswith("Theme:"):
                    theme = line.replace("Theme:", "").strip()
                elif line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.replace("Confidence:", "").strip())
                    except ValueError:
                        confidence = 0.5

            return {
                "theme": theme or "Unidentified theme",
                "summary": summary or content[:200],
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error extracting cluster theme: {e}")
            raise

    @staticmethod
    async def generate_trading_idea(
        cluster_theme: str,
        article_titles: List[str],
        article_summaries: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Generate trading idea from news cluster."""
        try:
            articles_text = "\n".join([
                f"- {title}: {summary[:100]}"
                for title, summary in zip(article_titles, article_summaries)
            ])

            prompt = f"""Analyze this cluster of related financial news articles and generate a specific trading idea if viable:

Theme: {cluster_theme}

Articles:
{articles_text}

Provide your analysis in this format:
Idea: [Specific, actionable trading idea or "NO_IDEA" if no viable opportunity]
Rationale: [Why this makes sense based on the news]
Instruments: [Comma-separated list of specific stocks, ETFs, or assets]
Direction: [long, short, or neutral]
Time Horizon: [short, medium, or long]
Confidence: [0-1 score of conviction]

If there is no clear trading opportunity, respond with just: NO_IDEA"""

            response = client.chat.completions.create(
                model=settings.completion_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert trading analyst who generates specific, actionable trading ideas from financial news. Only suggest ideas with clear catalysts and risk/reward profiles. Be conservative - if there's no clear opportunity, say NO_IDEA."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )

            content = response.choices[0].message.content.strip()

            # Check for NO_IDEA
            if "NO_IDEA" in content:
                logger.info(f"No viable trading idea for cluster: {cluster_theme}")
                return None

            # Parse response
            lines = content.split("\n")
            idea = ""
            rationale = ""
            instruments = []
            direction = "neutral"
            time_horizon = "medium"
            confidence = 0.5

            for line in lines:
                if line.startswith("Idea:"):
                    idea = line.replace("Idea:", "").strip()
                elif line.startswith("Rationale:"):
                    rationale = line.replace("Rationale:", "").strip()
                elif line.startswith("Instruments:"):
                    instruments_str = line.replace("Instruments:", "").strip()
                    instruments = [i.strip() for i in instruments_str.split(",") if i.strip()]
                elif line.startswith("Direction:"):
                    dir_value = line.replace("Direction:", "").strip().lower()
                    if dir_value in ["long", "short", "neutral"]:
                        direction = dir_value
                elif line.startswith("Time Horizon:"):
                    time_horizon = line.replace("Time Horizon:", "").strip().lower()
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.replace("Confidence:", "").strip())
                    except ValueError:
                        confidence = 0.5

            if not idea or not rationale:
                logger.warning(f"Incomplete trading idea generated for: {cluster_theme}")
                return None

            return {
                "idea": idea,
                "rationale": rationale,
                "instruments": instruments,
                "direction": direction,
                "time_horizon": time_horizon,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error generating trading idea: {e}")
            return None

    @staticmethod
    async def test_connection() -> bool:
        """Test OpenAI API connection."""
        try:
            # Simple test with a minimal embedding
            response = client.embeddings.create(
                model=settings.embedding_model,
                input="test"
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
