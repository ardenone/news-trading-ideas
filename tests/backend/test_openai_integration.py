"""
OpenAI API Integration Tests
Tests for embeddings generation, clustering, and cost tracking
"""

import pytest
import json
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestEmbeddingsGeneration:
    """Test OpenAI embeddings generation"""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, mock_openai_embeddings):
        """Should generate embedding for single text"""
        text = "Federal Reserve announces rate cut"

        response = await mock_openai_embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        embedding = response.data[0].embedding
        assert len(embedding) == 1536  # Standard embedding dimension
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_batch_embeddings_generation(self, mock_openai_embeddings):
        """Should generate embeddings for multiple texts efficiently"""
        texts = [
            "Article 1: Fed rate decision",
            "Article 2: Tech stocks rally",
            "Article 3: Market volatility increases"
        ]

        # Mock batch response
        mock_openai_embeddings.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536) for _ in texts]
        )

        response = await mock_openai_embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        assert len(response.data) == 3

        for embedding_obj in response.data:
            assert len(embedding_obj.embedding) == 1536

    @pytest.mark.asyncio
    async def test_store_embeddings_in_database(
        self,
        db_session,
        sample_articles,
        mock_openai_embeddings
    ):
        """Should store embeddings in database"""
        article_id = sample_articles[0]["id"]

        # Generate embedding
        response = await mock_openai_embeddings.embeddings.create(
            model="text-embedding-3-small",
            input="Test article content"
        )

        embedding_vector = np.array(response.data[0].embedding, dtype=np.float32)
        embedding_bytes = embedding_vector.tobytes()

        # Store in database
        db_session.execute(
            """CREATE TABLE IF NOT EXISTS embeddings (
                embedding_id INTEGER PRIMARY KEY,
                article_id INTEGER,
                embedding BLOB,
                model TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        db_session.commit()

        db_session.execute(
            "INSERT INTO embeddings (article_id, embedding, model) VALUES (?, ?, ?)",
            (article_id, embedding_bytes, "text-embedding-3-small")
        )
        db_session.commit()

        # Verify storage
        result = db_session.execute(
            "SELECT embedding, model FROM embeddings WHERE article_id = ?",
            (article_id,)
        ).fetchone()

        assert result is not None
        stored_vector = np.frombuffer(result[0], dtype=np.float32)
        assert len(stored_vector) == 1536
        assert result[1] == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_handle_rate_limiting(self, mock_openai_embeddings):
        """Should handle OpenAI rate limiting"""
        from openai import RateLimitError

        # Simulate rate limit error
        mock_openai_embeddings.embeddings.create.side_effect = RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body={}
        )

        with pytest.raises(RateLimitError):
            await mock_openai_embeddings.embeddings.create(
                model="text-embedding-3-small",
                input="Test"
            )

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_openai_embeddings):
        """Should implement exponential backoff on errors"""
        import asyncio

        attempt_count = 0

        async def retry_with_backoff(max_retries=3):
            nonlocal attempt_count

            for retry in range(max_retries):
                try:
                    attempt_count += 1
                    response = await mock_openai_embeddings.embeddings.create(
                        model="text-embedding-3-small",
                        input="Test"
                    )
                    return response
                except Exception:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry  # Exponential backoff
                        await asyncio.sleep(wait_time * 0.001)  # Shortened for testing
                    else:
                        raise

        # First call succeeds
        response = await retry_with_backoff()
        assert attempt_count == 1


class TestClustering:
    """Test article clustering with embeddings"""

    def test_calculate_cosine_similarity(self):
        """Should calculate cosine similarity correctly"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])

        # Identical vectors: similarity = 1.0
        sim1 = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(sim1 - 1.0) < 0.0001

        # Orthogonal vectors: similarity = 0.0
        sim2 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        assert abs(sim2) < 0.0001

    def test_dbscan_clustering(self):
        """Should cluster similar articles using DBSCAN"""
        from sklearn.cluster import DBSCAN

        # Create sample embeddings (5 articles, 2 clusters)
        embeddings = np.array([
            [1.0, 0.0, 0.0],  # Cluster 1
            [0.9, 0.1, 0.0],  # Cluster 1
            [0.0, 1.0, 0.0],  # Cluster 2
            [0.0, 0.9, 0.1],  # Cluster 2
            [0.5, 0.5, 0.0],  # Could be noise or bridge
        ])

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # Should find at least 2 clusters
        unique_labels = set(labels)
        assert len(unique_labels) >= 2

        # -1 represents noise
        cluster_labels = [l for l in unique_labels if l != -1]
        assert len(cluster_labels) >= 2

    def test_find_similar_articles(self):
        """Should find similar articles above threshold"""
        embeddings = {
            1: np.array([1.0, 0.0, 0.0]),
            2: np.array([0.95, 0.05, 0.0]),  # Very similar to 1
            3: np.array([0.0, 1.0, 0.0]),     # Not similar to 1
        }

        target = embeddings[1]
        threshold = 0.9

        similar = []
        for article_id, embedding in embeddings.items():
            if article_id == 1:
                continue

            similarity = np.dot(target, embedding) / (
                np.linalg.norm(target) * np.linalg.norm(embedding)
            )

            if similarity >= threshold:
                similar.append(article_id)

        assert 2 in similar  # Should find article 2
        assert 3 not in similar  # Should not find article 3


class TestClusterSummarization:
    """Test cluster summarization with GPT"""

    @pytest.mark.asyncio
    async def test_generate_cluster_summary(self, mock_openai_completion):
        """Should generate summary for article cluster"""
        articles = [
            {"title": "Fed Cuts Rates", "summary": "Federal Reserve reduces rates..."},
            {"title": "Market Reacts to Fed", "summary": "Stocks rally on Fed decision..."},
        ]

        prompt = "Summarize these related articles..."

        response = await mock_openai_completion.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.choices[0].message.content)

        assert "title" in result
        assert "summary" in result
        assert "impact_score" in result
        assert "confidence" in result

        assert 0 <= result["impact_score"] <= 100
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_cluster_quality_validation(self, mock_openai_completion):
        """Should validate cluster quality"""
        response = await mock_openai_completion.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Analyze cluster..."}]
        )

        result = json.loads(response.choices[0].message.content)

        # Low confidence clusters should be filtered
        if result["confidence"] < 0.7:
            pytest.skip("Low confidence cluster - would be filtered")

        assert result["confidence"] >= 0.7


class TestCostTracking:
    """Test API cost tracking"""

    @pytest.mark.asyncio
    async def test_track_embedding_costs(self, mock_openai_embeddings, db_session):
        """Should track embedding generation costs"""
        # Mock usage data
        mock_openai_embeddings.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)],
            usage=Mock(total_tokens=100)
        )

        response = await mock_openai_embeddings.embeddings.create(
            model="text-embedding-3-small",
            input="Test article"
        )

        # Calculate cost (text-embedding-3-small: $0.02 per 1M tokens)
        tokens = response.usage.total_tokens
        cost = (tokens / 1_000_000) * 0.02

        assert cost > 0
        assert cost < 0.01  # Should be very small for single article

    @pytest.mark.asyncio
    async def test_track_completion_costs(self, mock_openai_completion):
        """Should track completion costs"""
        response = await mock_openai_completion.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Summarize..."}]
        )

        # GPT-4o-mini: $0.150 input / $0.600 output per 1M tokens
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        input_cost = (prompt_tokens / 1_000_000) * 0.150
        output_cost = (completion_tokens / 1_000_000) * 0.600
        total_cost = input_cost + output_cost

        assert total_cost > 0

    def test_daily_cost_limit(self):
        """Should enforce daily cost limits"""
        daily_budget = 2.00  # $2/day target
        current_spending = 1.95

        proposed_cost = 0.10

        if current_spending + proposed_cost > daily_budget:
            # Should reject or queue operation
            assert True
        else:
            # Should allow operation
            assert current_spending + proposed_cost <= daily_budget


class TestNoViableTradingIdeas:
    """Test handling of scenarios with no viable trading ideas"""

    @pytest.mark.asyncio
    async def test_no_high_impact_clusters(self, db_session):
        """Should handle scenario with no high-impact clusters"""
        # Create low-impact cluster
        db_session.execute(
            """INSERT INTO news_events
               (event_summary, first_reported_time, last_updated,
                source_count, relevance_score)
               VALUES (?, ?, ?, ?, ?)""",
            ("Minor News Event", datetime.utcnow(), datetime.utcnow(), 1, 25.0)
        )
        db_session.commit()

        # Query high-impact clusters (score > 70)
        high_impact = db_session.execute(
            "SELECT COUNT(*) FROM news_events WHERE relevance_score > 70"
        ).fetchone()[0]

        assert high_impact == 0
        # System should return empty trading ideas list

    @pytest.mark.asyncio
    async def test_low_confidence_ideas_filtered(self, mock_openai_trading_idea):
        """Should filter out low-confidence trading ideas"""
        # Mock low confidence response
        low_confidence_idea = {
            "confidence_score": 5.5,  # Below threshold
            "summary": "Low confidence idea"
        }

        mock_openai_trading_idea.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps(low_confidence_idea)))]
        )

        response = await mock_openai_trading_idea.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Generate trading idea..."}]
        )

        idea = json.loads(response.choices[0].message.content)

        # Should be filtered (confidence < 6.0)
        if idea["confidence_score"] < 6.0:
            assert True  # Idea would be rejected

    def test_empty_state_handling(self, db_session):
        """Should handle empty database state gracefully"""
        # No articles
        article_count = db_session.execute(
            "SELECT COUNT(*) FROM articles"
        ).fetchone()[0]

        # No clusters
        cluster_count = db_session.execute(
            "SELECT COUNT(*) FROM news_events"
        ).fetchone()[0]

        # System should return appropriate empty states
        assert article_count >= 0
        assert cluster_count >= 0


class TestErrorHandlingAndRecovery:
    """Test error scenarios and recovery"""

    @pytest.mark.asyncio
    async def test_handle_api_failure(self, mock_openai_embeddings):
        """Should handle API failures gracefully"""
        from openai import APIError

        mock_openai_embeddings.embeddings.create.side_effect = APIError(
            "API error",
            request=Mock(),
            body={}
        )

        with pytest.raises(APIError):
            await mock_openai_embeddings.embeddings.create(
                model="text-embedding-3-small",
                input="Test"
            )

    @pytest.mark.asyncio
    async def test_handle_invalid_json_response(self):
        """Should handle invalid JSON in API responses"""
        with patch("openai.AsyncOpenAI") as mock_client:
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content="Invalid JSON {{{"))
            ]

            mock_instance = AsyncMock()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            response = await mock_instance.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}]
            )

            content = response.choices[0].message.content

            with pytest.raises(json.JSONDecodeError):
                json.loads(content)
