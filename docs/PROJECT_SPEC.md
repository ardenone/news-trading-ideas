# News Trading Ideas MVP - Project Specification

## Overview

A Docker-based platform that ingests RSS news feeds, clusters related articles using OpenAI, and generates trading ideas based on news analysis.

## Technical Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React
- **AI/ML:** OpenAI API (clustering + trading ideas)
- **Database:** SQLite (development), PostgreSQL-ready
- **Container:** Docker (single container)
- **Deployment:** GitHub Actions CI/CD

## Architecture

### Single Container Design

```
┌─────────────────────────────────────┐
│   Docker Container (Port 8000)      │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   FastAPI    │  │    React    │ │
│  │   Backend    │  │   Frontend  │ │
│  │   (API)      │  │   (Static)  │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │                 │         │
│  ┌──────▼─────────────────▼──────┐ │
│  │   OpenAI Integration Layer    │ │
│  └──────────────┬──────────────┬──┘ │
│                 │              │     │
│  ┌──────────────▼──┐  ┌────────▼──┐ │
│  │  RSS Ingestion  │  │  Database │ │
│  └─────────────────┘  └───────────┘ │
└─────────────────────────────────────┘
```

## Core Features

### 1. RSS Feed Ingestion
- Automatic polling (configurable interval)
- Support multiple RSS sources
- Deduplication logic
- Timestamp tracking

### 2. News Clustering
- OpenAI-powered semantic clustering
- Group related articles
- Extract key themes
- Relevance scoring

### 3. Trading Ideas Generation
- Analyze clustered news
- Generate actionable trading ideas
- Confidence scoring
- Handle "no viable ideas" gracefully

### 4. User Interface
- Display news clusters
- Show trading ideas
- Filter by date/source
- Responsive design

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /api/status` - System status

### News Management
- `GET /api/news` - List news articles
- `GET /api/news/{id}` - Get article details
- `POST /api/news/refresh` - Trigger RSS refresh

### Clustering
- `GET /api/clusters` - List news clusters
- `GET /api/clusters/{id}` - Get cluster details
- `POST /api/clusters/generate` - Generate clusters

### Trading Ideas
- `GET /api/ideas` - List trading ideas
- `GET /api/ideas/{id}` - Get idea details
- `POST /api/ideas/generate` - Generate ideas from clusters

## Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Application
APP_ENV=production
LOG_LEVEL=info
RSS_POLL_INTERVAL=300

# Database
DATABASE_URL=sqlite:///./news.db

# RSS Feeds
RSS_FEEDS=https://feed1.com,https://feed2.com
```

## Testing Requirements

### Backend Tests (>80% coverage)
- Unit tests for all endpoints
- Integration tests for OpenAI
- RSS ingestion tests
- Database operation tests

### Frontend Tests
- Component rendering tests
- User interaction tests
- API integration tests

### E2E Tests
- Full workflow tests
- Docker container tests

## Success Criteria

1. ✅ Single Docker container builds successfully
2. ✅ Container starts without errors
3. ✅ Health check endpoint responds
4. ✅ API endpoints functional
5. ✅ Frontend loads in browser
6. ✅ RSS feeds ingested automatically
7. ✅ News clustering works
8. ✅ Trading ideas generated
9. ✅ "No viable ideas" handled gracefully
10. ✅ All tests pass (>80% coverage)
11. ✅ CI/CD pipeline configured
12. ✅ Documentation complete

## Deployment

### GitHub Repository
- Organization: ardenone
- Repository: news-trading-ideas
- Branch strategy: main (protected)

### CI/CD Pipeline
- Automated testing on PR
- Docker build on merge
- Deployment to production

## Timeline

- **Phase 1:** Architecture & Design (Day 1)
- **Phase 2:** Implementation (Day 1-2)
- **Phase 3:** Testing & Refinement (Day 2-3)
- **Phase 4:** Deployment (Day 3)

## Constraints

- Single container deployment only
- Must use OpenAI API (no alternatives)
- Port 8000 exposed for HTTP
- SQLite for development (easy migration to PostgreSQL)
- Environment variables for configuration
- No secrets in code/repository

---
*Version: 1.0 | Date: 2025-10-23*
