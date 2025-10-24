# Quick Start Guide - News Trading Ideas Backend

## Installation & Setup

### 1. Install Dependencies

```bash
cd /home/jarden/news-trading-ideas/src/backend

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# IMPORTANT: Add this line to your .env:
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Note: Your existing `/home/jarden/.env` has B2 keys but needs `OPENAI_API_KEY` added.

### 3. Create Database

```bash
# Create data directory
mkdir -p data

# Initialize database (run from backend directory)
poetry run python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# Seed with priority RSS feeds
poetry run python scripts/seed_feeds.py
```

### 4. Run the Server

```bash
# Development mode with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: http://localhost:8000

## Testing the API

### Using the Interactive Docs

Visit http://localhost:8000/docs for Swagger UI where you can test all endpoints interactively.

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List RSS feeds
curl http://localhost:8000/api/v1/feeds/

# List articles
curl http://localhost:8000/api/v1/articles/?limit=10

# List events (sorted by relevance)
curl http://localhost:8000/api/v1/events/

# List trading ideas
curl http://localhost:8000/api/v1/ideas/

# Manually refresh a feed
curl -X POST http://localhost:8000/api/v1/feeds/1/refresh
```

## Background Jobs

The following jobs run automatically when the server starts:

1. **RSS Feed Fetcher** (every 5 minutes)
   - Fetches all active feeds
   - Creates new articles
   - Deduplicates by URL and content hash

2. **Article Clusterer** (every 10 minutes)
   - Groups pending articles into events using GPT-4o-mini
   - Calculates relevance scores
   - Marks stale events

3. **Trading Idea Generator** (every 10 minutes)
   - Generates ideas for top 10 events using GPT-4
   - Handles "no viable trade" scenarios gracefully
   - Tracks API costs

## Monitoring

### Check Logs

The application uses structured JSON logging. All logs go to stdout.

```bash
# View logs
poetry run uvicorn app.main:app --reload --log-level info
```

### Check Database

```bash
# Open SQLite database
sqlite3 data/news_trading.db

# View tables
.tables

# Count articles
SELECT COUNT(*) FROM articles;

# View recent events
SELECT event_id, event_summary, relevance_score FROM news_events ORDER BY created_at DESC LIMIT 10;

# View trading ideas
SELECT idea_id, headline, confidence_score FROM trading_ideas ORDER BY generated_at DESC;

# Exit
.exit
```

## OpenAI API Cost Tracking

All OpenAI API calls are tracked with token usage and cost:

```sql
-- View API costs from trading_ideas table
SELECT
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    COUNT(*) as ideas_generated
FROM trading_ideas;
```

Daily cost limit is set to $5.00 (configurable in `.env` with `MAX_DAILY_OPENAI_COST`).

## Common Tasks

### Add New RSS Feed

```bash
curl -X POST http://localhost:8000/api/v1/feeds/ \
  -H "Content-Type: application/json" \
  -d '{
    "feed_url": "https://www.benzinga.com/feed",
    "source_name": "Benzinga",
    "category": "finance",
    "update_interval": 300,
    "is_active": true
  }'
```

### Manually Trigger Jobs

```python
# Run from Python shell
poetry shell
python

from app.database import AsyncSessionLocal
from app.services.rss_ingestion import rss_service
from app.services.clustering import clustering_service
from app.services.idea_generation import idea_service
import asyncio

async def run_jobs():
    async with AsyncSessionLocal() as session:
        # Fetch feeds
        articles = await rss_service.fetch_all_feeds(session)
        print(f"Fetched {articles} new articles")

        # Cluster articles
        events = await clustering_service.cluster_pending_articles(session)
        print(f"Created {events} events")

        # Generate ideas
        ideas = await idea_service.generate_ideas_for_top_events(session)
        print(f"Generated {ideas} trading ideas")

asyncio.run(run_jobs())
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app tests/

# Run specific test
poetry run pytest tests/test_feeds.py -v
```

## Troubleshooting

### Database Locked Error

If you get "database is locked" errors:

```bash
# Check if WAL mode is enabled
sqlite3 data/news_trading.db "PRAGMA journal_mode;"
# Should output: wal

# If not WAL, enable it
sqlite3 data/news_trading.db "PRAGMA journal_mode=WAL;"
```

### OpenAI API Errors

Check your API key is set correctly:

```bash
# Verify in .env
cat .env | grep OPENAI_API_KEY

# Test API key manually
poetry shell
python
from openai import OpenAI
client = OpenAI()
response = client.models.list()
print(response)
```

### No Articles Being Fetched

Check feed status:

```sql
sqlite3 data/news_trading.db

SELECT feed_id, source_name, last_fetched, error_count, last_error
FROM rss_feeds
WHERE is_active = 1;
```

If `error_count` > 0, check `last_error` for details.

## Production Deployment

### Using uvicorn directly

```bash
poetry run uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Using Docker (create Dockerfile)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY app ./app

# Create data directory
RUN mkdir -p /app/data

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

1. Add your OPENAI_API_KEY to `/home/jarden/.env`
2. Run the seed script to add RSS feeds
3. Start the server and visit http://localhost:8000/docs
4. Monitor the background jobs as they fetch and process news
5. Check `/api/v1/ideas/` after ~15 minutes for generated trading ideas

## Support

For issues or questions, refer to:
- Main README: `/home/jarden/news-trading-ideas/src/backend/README.md`
- Architecture docs: `/home/jarden/news-trading-ideas/architecture/`
- OpenAI docs: `/home/jarden/news-trading-ideas/openai_docs/responses.md`
