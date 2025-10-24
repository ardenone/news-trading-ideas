# News Trading Ideas MVP

AI-powered news clustering and trading ideas generation platform built with FastAPI, React, and OpenAI.

## Features

- **Automatic RSS News Ingestion**: Polls configured RSS feeds every 5 minutes
- **AI-Powered News Clustering**: Uses OpenAI embeddings to cluster related news articles
- **Trading Ideas Generation**: Generates actionable trading ideas from news clusters using GPT-4
- **Real-time Monitoring**: Health checks and system status monitoring
- **Single Docker Container**: Easy deployment with all services in one container

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 + Vite
- **AI/ML**: OpenAI API (embeddings + GPT-4)
- **Database**: SQLite (development), PostgreSQL-ready
- **Server**: NGINX reverse proxy + Uvicorn
- **Container**: Docker with multi-stage build

## Quick Start

### Prerequisites

- Docker
- OpenAI API key

### Running with Docker

1. Clone the repository:
```bash
git clone https://github.com/ardenone/news-trading-ideas.git
cd news-trading-ideas
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Build and run:
```bash
docker build -t news-trading-ideas .
docker run -d \
  --name news-trading-ideas \
  -p 8000:8000 \
  --env-file .env \
  news-trading-ideas
```

4. Access the application:
- UI: http://localhost:8000
- API docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

## Configuration

Environment variables (`.env`):

```env
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
RSS_POLL_INTERVAL=300
RSS_FEEDS=https://feed1.com,https://feed2.com
DATABASE_URL=sqlite:///./news.db
LOG_LEVEL=info
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system architecture
- [Project Specification](docs/PROJECT_SPEC.md) - Requirements and features
- [Progress](docs/PROGRESS.md) - Development status

## License

MIT

---

Built with [Claude Flow](https://github.com/ruvnet/claude-flow) orchestration
