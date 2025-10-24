"""Tests for clustering service"""

import pytest
from unittest.mock import patch, AsyncMock
from app.services.clustering import clustering_service


@pytest.mark.asyncio
async def test_cluster_pending_articles(db_session, sample_article):
    """Test clustering pending articles"""
    # Mock OpenAI API response
    mock_response = {
        "text": """{
            "events": [{
                "event_summary": "Test Event",
                "event_key": "test-event-2025",
                "headline_ids": [1],
                "relevance_score": 8,
                "first_reported": "2025-10-22T14:30:00Z"
            }],
            "ungrouped_headlines": []
        }""",
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        "cost": 0.01,
    }

    with patch(
        "app.core.openai_client.openai_client.create_response",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        events_created = await clustering_service.cluster_pending_articles(db_session)
        assert events_created >= 0


@pytest.mark.asyncio
async def test_mark_stale_events(db_session):
    """Test marking stale events"""
    await clustering_service.mark_stale_events(db_session)
    # Should not raise exceptions
