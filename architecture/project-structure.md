# Project Structure Template

**Version:** 1.0
**Date:** October 22, 2025

---

## Complete Directory Structure

```
news-trading-ideas/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Caddyfile
│
├── backend/                          # Python FastAPI backend
│   ├── pyproject.toml                # Poetry dependencies
│   ├── poetry.lock
│   ├── Dockerfile
│   ├── .env
│   ├── alembic.ini                   # Database migrations config
│   │
│   ├── alembic/                      # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial.py
│   │
│   ├── app/                          # Main application
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── config.py                 # Configuration
│   │   ├── database.py               # Database setup
│   │   ├── dependencies.py           # Shared dependencies
│   │   │
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── feed.py
│   │   │   ├── article.py
│   │   │   ├── embedding.py
│   │   │   ├── cluster.py
│   │   │   └── trading_idea.py
│   │   │
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── feed.py
│   │   │   ├── article.py
│   │   │   ├── cluster.py
│   │   │   └── trading_idea.py
│   │   │
│   │   ├── api/                      # API routes
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── feeds.py
│   │   │       ├── articles.py
│   │   │       ├── clusters.py
│   │   │       ├── ideas.py
│   │   │       └── admin.py
│   │   │
│   │   ├── services/                 # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── rss_ingestion.py
│   │   │   ├── embedding.py
│   │   │   ├── clustering.py
│   │   │   ├── idea_generation.py
│   │   │   └── cost_tracking.py
│   │   │
│   │   ├── core/                     # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── openai_client.py
│   │   │   ├── cache.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── metrics.py
│   │   │
│   │   └── workers/                  # Background jobs
│   │       ├── __init__.py
│   │       ├── scheduler.py
│   │       ├── feed_poller.py
│   │       ├── ai_processor.py
│   │       └── maintenance.py
│   │
│   ├── tests/                        # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_feeds.py
│   │   ├── test_articles.py
│   │   ├── test_clustering.py
│   │   └── test_ideas.py
│   │
│   └── scripts/                      # Utility scripts
│       ├── init_db.py
│       ├── seed_data.py
│       ├── backup_db.sh
│       └── estimate_costs.py
│
├── frontend/                         # React frontend
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── .env
│   │
│   ├── public/                       # Static assets
│   │   ├── favicon.ico
│   │   └── logo.svg
│   │
│   ├── src/
│   │   ├── main.tsx                  # App entry
│   │   ├── App.tsx                   # Root component
│   │   ├── index.css                 # Global styles
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── api/                      # API client
│   │   │   ├── client.ts
│   │   │   ├── feeds.ts
│   │   │   ├── articles.ts
│   │   │   ├── clusters.ts
│   │   │   └── ideas.ts
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── ...
│   │   │   ├── ArticleCard.tsx
│   │   │   ├── ClusterCard.tsx
│   │   │   ├── IdeaCard.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── Pagination.tsx
│   │   │   └── Layout.tsx
│   │   │
│   │   ├── pages/                    # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── News.tsx
│   │   │   ├── Ideas.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── NotFound.tsx
│   │   │
│   │   ├── hooks/                    # Custom hooks
│   │   │   ├── useArticles.ts
│   │   │   ├── useClusters.ts
│   │   │   ├── useIdeas.ts
│   │   │   └── useFeeds.ts
│   │   │
│   │   ├── types/                    # TypeScript types
│   │   │   ├── article.ts
│   │   │   ├── cluster.ts
│   │   │   ├── idea.ts
│   │   │   └── feed.ts
│   │   │
│   │   └── lib/                      # Utilities
│   │       ├── utils.ts
│   │       ├── constants.ts
│   │       └── formatters.ts
│   │
│   └── tests/                        # Frontend tests
│       ├── setup.ts
│       └── components/
│           ├── ArticleCard.test.tsx
│           └── ClusterCard.test.tsx
│
├── data/                             # Data directory (gitignored)
│   ├── app.db                        # SQLite database
│   └── backups/
│
├── logs/                             # Logs directory (gitignored)
│   ├── app.log
│   └── error.log
│
├── docs/                             # Documentation
│   ├── api.md
│   ├── architecture.md
│   ├── deployment.md
│   └── development.md
│
└── monitoring/                       # Monitoring configs (optional)
    ├── prometheus.yml
    └── grafana/
        └── dashboards/
```

---

## Key Files Content

### Root Configuration

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

**.gitignore**
```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# Node.js
node_modules/
dist/
.pnpm-debug.log

# Database
data/
*.db
*.db-*

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
build/
*.egg-info/
```

**.env.example**
```env
# Backend
DATABASE_URL=sqlite:///./data/app.db
OPENAI_API_KEY=sk-your-api-key-here
LOG_LEVEL=INFO
ENABLE_CORS=true

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Optional
SENTRY_DSN=
PROMETHEUS_ENABLED=false
```

---

## Backend Files

### backend/pyproject.toml

```toml
[tool.poetry]
name = "news-trading-backend"
version = "1.0.0"
description = "News aggregation and trading ideas backend"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
pydantic = "^2.4.0"
pydantic-settings = "^2.0.0"
openai = "^1.3.0"
feedparser = "^6.0.0"
httpx = "^0.25.0"
apscheduler = "^3.10.0"
python-dateutil = "^2.8.0"
scikit-learn = "^1.3.0"
numpy = "^1.26.0"
prometheus-client = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.10.0"
ruff = "^0.1.0"
mypy = "^1.6.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### backend/app/config.py

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Application
    APP_NAME: str = "News Trading Ideas"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Scheduler
    FEED_POLL_INTERVAL: int = 300  # seconds
    AI_PROCESS_INTERVAL: int = 600  # seconds

    # Clustering
    CLUSTERING_THRESHOLD: float = 0.8
    MIN_CLUSTER_SIZE: int = 2

    # API Limits
    MAX_DAILY_OPENAI_COST: float = 5.0  # dollars

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### backend/app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create engine with optimizations
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)

# Configure SQLite optimizations
with engine.connect() as conn:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB
    conn.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Frontend Files

### frontend/package.json

```json
{
  "name": "news-trading-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.18.0",
    "@tanstack/react-query": "^5.8.0",
    "axios": "^1.6.0",
    "date-fns": "^2.30.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "lucide-react": "^0.292.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.4"
  }
}
```

### frontend/vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
        },
      },
    },
  },
})
```

### frontend/tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
    },
  },
  plugins: [],
}
```

---

## Documentation Files

### docs/development.md

```markdown
# Development Guide

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Poetry
- pnpm

## Setup

### Backend
\`\`\`bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
\`\`\`

### Frontend
\`\`\`bash
cd frontend
pnpm install
pnpm dev
\`\`\`

## Testing

### Backend
\`\`\`bash
cd backend
poetry run pytest
poetry run pytest --cov=app tests/
\`\`\`

### Frontend
\`\`\`bash
cd frontend
pnpm test
\`\`\`

## Code Quality

### Backend
\`\`\`bash
poetry run black .
poetry run ruff check .
poetry run mypy .
\`\`\`

### Frontend
\`\`\`bash
pnpm lint
pnpm type-check
\`\`\`
```

---

## Scripts

### backend/scripts/init_db.py

```python
#!/usr/bin/env python
"""Initialize database with schema and seed data"""

from app.database import engine, Base
from app.models import Feed, Article, Cluster, TradingIdea

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()
```

### backend/scripts/backup_db.sh

```bash
#!/bin/bash
# Backup SQLite database

BACKUP_DIR="./data/backups"
DB_PATH="./data/app.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

sqlite3 $DB_PATH ".backup ${BACKUP_DIR}/backup_${DATE}.db"
gzip ${BACKUP_DIR}/backup_${DATE}.db

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}/backup_${DATE}.db.gz"
```

---

## Summary

This project structure provides:

1. **Clear separation of concerns**: Backend, frontend, docs, scripts
2. **Scalable architecture**: Easy to add new features
3. **Best practices**: Testing, linting, type checking
4. **Docker support**: Easy deployment
5. **Documentation**: Comprehensive guides
6. **Development tools**: Scripts for common tasks

All files are organized logically and follow industry standards for Python (FastAPI) and React (Vite) projects.

**Last Updated:** October 22, 2025
