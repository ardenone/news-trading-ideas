"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "openai" in data


def test_list_news(client):
    """Test list news endpoint."""
    response = client.get("/api/news")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert isinstance(data["articles"], list)


def test_list_clusters(client):
    """Test list clusters endpoint."""
    response = client.get("/api/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "clusters" in data
    assert "total" in data


def test_list_ideas(client):
    """Test list ideas endpoint."""
    response = client.get("/api/ideas")
    assert response.status_code == 200
    data = response.json()
    assert "ideas" in data
    assert "total" in data


def test_refresh_news(client):
    """Test RSS refresh endpoint."""
    response = client.post("/api/news/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data


def test_generate_clusters(client):
    """Test cluster generation endpoint."""
    response = client.post(
        "/api/clusters/generate",
        json={"min_articles": 5, "force": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_generate_ideas(client):
    """Test ideas generation endpoint."""
    response = client.post(
        "/api/ideas/generate",
        json={"cluster_ids": None, "force": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
