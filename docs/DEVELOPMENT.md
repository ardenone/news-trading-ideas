# Development Guide

## Overview

This guide covers local development setup for the News Trading Ideas MVP platform.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git
- Visual Studio Code (recommended)

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/ardenone/news-trading-ideas.git
cd news-trading-ideas

# Create environment file
cp .env.example .env
nano .env  # Add your API keys
```

### 2. Local Development (Without Docker)

#### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Initialize database
python -c "from database import init_db; init_db()"

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### 3. Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

#### Backend Changes

```bash
# Edit Python files in backend/
cd backend

# Run tests
pytest

# Run linting
black .
flake8 .
isort .

# Type checking
mypy .
```

#### Frontend Changes

```bash
# Edit React components in frontend/src/
cd frontend

# Run development server
npm run dev

# Run linting
npm run lint

# Run tests
npm test

# Build
npm run build
```

### 3. Test Changes

```bash
# Test with Docker
docker-compose up --build

# Access application
open http://localhost:8000

# Run tests in container
docker-compose exec app pytest
```

### 4. Commit and Push

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add news clustering endpoint"

# Push to GitHub
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Go to GitHub repository
- Click "New Pull Request"
- Select your feature branch
- Fill in PR template
- Wait for CI/CD checks to pass

## Project Structure

```
news-trading-ideas/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Data models
│   ├── database.py          # Database configuration
│   ├── clustering.py        # News clustering logic
│   ├── trading_ideas.py     # Trading ideas generation
│   ├── requirements.txt     # Python dependencies
│   └── tests/               # Backend tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── styles/          # CSS/styling
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── docs/
│   ├── DOCKER.md            # Docker documentation
│   ├── DEPLOYMENT.md        # Deployment guide
│   └── DEVELOPMENT.md       # This file
├── .github/
│   └── workflows/
│       └── docker-build-test.yml  # CI/CD pipeline
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Local development
├── docker-entrypoint.sh     # Container initialization
└── .env                     # Environment variables
```

## API Development

### Adding New Endpoint

```python
# backend/main.py
@app.post("/api/new-endpoint")
async def new_endpoint(request: RequestModel):
    """
    Add endpoint description.
    """
    try:
        # Implementation
        result = process_data(request.data)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in new endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Testing Endpoint

```bash
# Using curl
curl -X POST http://localhost:8000/api/new-endpoint \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'

# Using httpie
http POST localhost:8000/api/new-endpoint data="test"

# Using Python requests
python -c "
import requests
r = requests.post('http://localhost:8000/api/new-endpoint',
                  json={'data': 'test'})
print(r.json())
"
```

## Frontend Development

### Adding New Component

```jsx
// frontend/src/components/NewComponent.jsx
import React, { useState, useEffect } from 'react';

export function NewComponent({ prop1, prop2 }) {
  const [state, setState] = useState(null);

  useEffect(() => {
    // Initialization logic
  }, []);

  return (
    <div className="new-component">
      {/* Component JSX */}
    </div>
  );
}
```

### API Integration

```javascript
// frontend/src/services/api.js
export async function fetchData(params) {
  const response = await fetch('/api/endpoint', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error('API request failed');
  }

  return response.json();
}
```

## Testing

### Backend Tests

```python
# backend/tests/test_clustering.py
import pytest
from clustering import cluster_articles

def test_cluster_articles():
    articles = [
        {"title": "Test 1", "content": "Content 1"},
        {"title": "Test 2", "content": "Content 2"},
    ]

    result = cluster_articles(articles)

    assert result is not None
    assert len(result) > 0
    assert "clusters" in result
```

Run tests:

```bash
# All tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Specific test
pytest backend/tests/test_clustering.py::test_cluster_articles

# Verbose output
pytest -v
```

### Frontend Tests

```javascript
// frontend/src/components/__tests__/NewComponent.test.jsx
import { render, screen } from '@testing-library/react';
import { NewComponent } from '../NewComponent';

test('renders component', () => {
  render(<NewComponent />);
  const element = screen.getByText(/expected text/i);
  expect(element).toBeInTheDocument();
});
```

Run tests:

```bash
# All tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## Code Quality

### Python

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Linting
flake8 backend/

# Type checking
mypy backend/

# Security check
bandit -r backend/
```

### JavaScript/React

```bash
# Linting
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type checking (if using TypeScript)
npm run type-check
```

## Database Management

### SQLite Development

```bash
# Access database
sqlite3 data/news_trading.db

# View tables
.tables

# View schema
.schema articles

# Query data
SELECT * FROM articles LIMIT 10;

# Exit
.quit
```

### Migrations

```bash
# Create migration
alembic revision -m "Add new column"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Debugging

### Backend Debugging

```python
# Add debug logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Using pdb

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

### Frontend Debugging

```javascript
// Console logging
console.log('Debug:', data);
console.error('Error:', error);

// React DevTools
// Install browser extension

// Redux DevTools (if using Redux)
// Install browser extension
```

## Environment Variables

### Development `.env`

```bash
# API Keys
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...

# Development settings
ENVIRONMENT=development
LOG_LEVEL=debug
DATABASE_URL=sqlite:///data/dev.db

# Optional: Override models
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small

# Frontend
VITE_API_URL=http://localhost:8000
```

### Loading in Python

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
```

### Loading in JavaScript

```javascript
// Vite automatically loads from .env
const apiUrl = import.meta.env.VITE_API_URL;
```

## Hot Reload

### Backend (Uvicorn)

```bash
# Automatic reload on file changes
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Vite)

```bash
# Automatic reload on file changes
npm run dev
```

### Docker Development

```yaml
# docker-compose.yml with hot reload
services:
  app:
    volumes:
      - ./backend:/app/backend
      - ./frontend/dist:/app/backend/static
```

## Performance Profiling

### Backend Profiling

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Memory Profiling

```python
# Using memory_profiler
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code
    pass
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Docker Build Fails

```bash
# Clean build
docker-compose build --no-cache

# Remove all containers
docker-compose down -v

# Prune system
docker system prune -a
```

#### Database Locked

```bash
# Stop all services
docker-compose down

# Remove database lock
rm data/news_trading.db-wal data/news_trading.db-shm

# Restart
docker-compose up
```

## Best Practices

1. **Code Style**
   - Follow PEP 8 for Python
   - Use ESLint for JavaScript
   - Write descriptive commit messages

2. **Testing**
   - Write tests for new features
   - Maintain >80% code coverage
   - Test edge cases

3. **Documentation**
   - Document complex functions
   - Update README for new features
   - Keep API docs current

4. **Security**
   - Never commit API keys
   - Validate all inputs
   - Use environment variables

5. **Performance**
   - Profile before optimizing
   - Cache frequently accessed data
   - Use async where appropriate

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## Support

For development questions:
- GitHub Issues: https://github.com/ardenone/news-trading-ideas/issues
- Documentation: `/home/jarden/news-trading-ideas/docs/`
