"""Tests for feed endpoints"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_feeds():
    """Test listing RSS feeds"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/feeds/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_feed():
    """Test creating a new feed"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        feed_data = {
            "feed_url": "https://example.com/feed.xml",
            "source_name": "Test Feed",
            "category": "finance",
            "update_interval": 300,
            "is_active": True,
        }
        response = await client.post("/api/v1/feeds/", json=feed_data)
        assert response.status_code == 201
        data = response.json()
        assert data["source_name"] == "Test Feed"


@pytest.mark.asyncio
async def test_get_feed(sample_feed):
    """Test getting a specific feed"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/feeds/{sample_feed.feed_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["feed_id"] == sample_feed.feed_id
