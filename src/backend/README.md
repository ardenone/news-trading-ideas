# News Trading Ideas Backend

FastAPI backend for the News Trading Ideas MVP platform.

## Features

- RSS feed ingestion with async HTTP
- OpenAI Responses API integration for clustering and trading ideas generation
- SQLite database with async SQLAlchemy
- APScheduler for background jobs
- Comprehensive error handling and cost tracking
- REST API with automatic OpenAPI docs

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- OpenAI API key

### Installation

```bash
# Install dependencies
cd /home/jarden/news-trading-ideas/src/backend
poetry install

# Copy environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Create data directory
mkdir -p data

# Run database migrations (if using Alembic)
poetry run alembic upgrade head
```

### Running

```bash
# Development server with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Feeds
- `GET /api/v1/feeds/` - List all RSS feeds
- `POST /api/v1/feeds/` - Create new feed
- `GET /api/v1/feeds/{id}` - Get feed details
- `POST /api/v1/feeds/{id}/refresh` - Manually refresh feed
- `DELETE /api/v1/feeds/{id}` - Delete feed

### Articles
- `GET /api/v1/articles/` - List articles (with filters)
- `GET /api/v1/articles/{id}` - Get article details

### Events
- `GET /api/v1/events/` - List news events (sorted by relevance)
- `GET /api/v1/events/{id}` - Get event details with articles

### Trading Ideas
- `GET /api/v1/ideas/` - List trading ideas
- `GET /api/v1/ideas/{id}` - Get trading idea details

### Health
- `GET /health` - Health check endpoint

## Background Jobs

The following jobs run automatically:

1. **Fetch RSS Feeds** (every 5 minutes)
   - Fetches all active feeds
   - Parses articles
   - Deduplicates by URL/content hash

2. **Cluster Articles** (every 10 minutes)
   - Groups pending articles into events using GPT-4o-mini
   - Updates event rankings
   - Marks stale events

3. **Generate Trading Ideas** (every 10 minutes)
   - Generates ideas for top 10 events using GPT-4
   - Handles "no viable trade" scenarios
   - Tracks API costs

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app tests/

# Run specific test file
poetry run pytest tests/test_feeds.py
```

## Database

SQLite database with the following tables:
- `rss_feeds` - RSS feed configurations
- `articles` - News articles from feeds
- `news_events` - Clustered events
- `event_articles` - Many-to-many mapping
- `trading_ideas` - Generated trading ideas
- `trade_strategies` - Specific trade strategies

## OpenAI API Usage

### Clustering (GPT-4o-mini)
- Cost: ~$0.002 per 100 headlines
- Batch size: 40 articles per call
- Temperature: 0.3 (consistent results)

### Trading Ideas (GPT-4)
- Cost: ~$0.15-0.25 per idea
- Temperature: 0.7 (creative strategies)
- Max tokens: 2000

### Cost Tracking
- Daily cost limit: $5.00 (configurable)
- Automatic cost calculation for all API calls
- Stored in database for audit trail

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `OPENAI_API_KEY` - Required
- `DATABASE_URL` - SQLite path
- `FEED_POLL_INTERVAL` - Seconds between RSS fetches
- `AI_PROCESS_INTERVAL` - Seconds between AI jobs
- `MAX_DAILY_OPENAI_COST` - Daily spending limit

## Project Structure

```
app/
├── api/
│   └── v1/           # API endpoints
├── core/             # Core utilities (OpenAI client)
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
│   ├── rss_ingestion.py
│   ├── clustering.py
│   └── idea_generation.py
├── workers/          # Background jobs
├── config.py         # Configuration
├── database.py       # Database setup
└── main.py          # FastAPI app

tests/
├── conftest.py      # Pytest fixtures
├── test_feeds.py
└── test_clustering.py
```

## License

Proprietary - All rights reserved
