# Test Suite - News Trading Ideas MVP

## 📋 Overview

Comprehensive test-driven development (TDD) suite for the News Trading Ideas platform, featuring backend, frontend, and integration tests with >80% coverage target.

## 🗂️ Test Structure

```
tests/
├── backend/              # Python/pytest backend tests
│   ├── conftest.py       # Fixtures and test configuration
│   ├── test_rss_ingestion.py
│   ├── test_openai_integration.py
│   ├── test_database.py
│   ├── test_clustering.py
│   ├── test_trading_ideas.py
│   └── test_api_endpoints.py
├── frontend/             # TypeScript/Vitest frontend tests
│   ├── components.test.tsx
│   └── api-client.test.ts
├── docker/               # Docker integration tests
│   └── test_container.sh
└── README.md            # This file
```

## 🚀 Quick Start

### Backend Tests (Python/pytest)

```bash
# Install dependencies
cd backend
poetry install --with dev

# Run all backend tests
poetry run pytest tests/

# Run with coverage
poetry run pytest --cov=app --cov-report=html tests/

# Run specific test file
poetry run pytest tests/backend/test_rss_ingestion.py

# Run specific test
poetry run pytest tests/backend/test_rss_ingestion.py::TestRSSFeedParsing::test_parse_valid_rss_feed

# Verbose output
poetry run pytest -v tests/

# Stop on first failure
poetry run pytest -x tests/
```

### Frontend Tests (TypeScript/Vitest)

```bash
# Install dependencies
cd frontend
pnpm install

# Run all frontend tests
pnpm test

# Run with coverage
pnpm test:coverage

# Watch mode (re-run on changes)
pnpm test:watch

# UI mode
pnpm test:ui
```

### Docker Integration Tests

```bash
# From project root
cd /home/jarden/news-trading-ideas

# Run Docker tests
./tests/docker/test_container.sh

# View test output
# Script will:
# 1. Build Docker image
# 2. Start container
# 3. Wait for health check
# 4. Test API endpoints
# 5. Check logs for errors
# 6. Cleanup
```

## 📊 Test Coverage Goals

- **Overall**: >80% code coverage
- **Backend**:
  - Models: >90%
  - Services: >85%
  - API endpoints: >80%
  - Database queries: >75%
- **Frontend**:
  - Components: >80%
  - API client: >90%
  - Utilities: >85%

## 🧪 Test Categories

### Unit Tests

Test individual functions and components in isolation:

```bash
# Backend
pytest tests/backend/test_rss_ingestion.py::TestArticleDeduplication

# Frontend
pnpm test components.test.tsx
```

### Integration Tests

Test interactions between components:

```bash
# Backend API integration
pytest tests/backend/test_api_endpoints.py

# Frontend API client integration
pnpm test api-client.test.ts
```

### End-to-End Tests

Test complete workflows:

```bash
# Docker container integration
./tests/docker/test_container.sh
```

## 🎯 Test Fixtures

### Backend Fixtures (conftest.py)

- `db_session` - In-memory SQLite database
- `sample_feeds` - Pre-populated RSS feeds
- `sample_articles` - Sample news articles
- `sample_cluster_data` - Sample event clusters
- `mock_openai_embeddings` - Mocked OpenAI embeddings API
- `mock_openai_completion` - Mocked OpenAI completion API
- `mock_rss_feed` - Mocked RSS feed parser
- `test_client` - FastAPI test client
- `performance_tracker` - Performance measurement utility

## 🔄 Iterative TDD Workflow

### Cycle 1: Build → Test → Fix

```bash
# 1. Build Docker image
docker build -t news-trading-ideas:test .

# 2. Run tests
pytest tests/
./tests/docker/test_container.sh

# 3. Review failures
# Check pytest output and Docker logs

# 4. Fix issues
# Update code based on test failures

# 5. Repeat until all tests pass
```

### Cycle 2: Test → Code → Refactor

```bash
# 1. Write test first (TDD)
# Create test in appropriate test file

# 2. Run test (should fail)
pytest tests/backend/test_new_feature.py

# 3. Write minimum code to pass
# Implement feature in app/

# 4. Refactor
# Improve code while keeping tests passing
```

## 📝 Test Examples

### Backend Test Example

```python
def test_create_feed(db_session):
    """Should create new RSS feed"""
    result = db_session.execute(
        """INSERT INTO rss_feeds (feed_url, source_name, category)
           VALUES (?, ?, ?)""",
        ("https://test.com/rss", "Test Feed", "tech")
    )
    db_session.commit()

    feed_id = result.lastrowid
    assert feed_id > 0
```

### Frontend Test Example

```typescript
it('should render article headline', () => {
  const mockArticle = {
    id: 1,
    headline: 'Fed Announces Rate Cut',
    source: 'Bloomberg'
  };

  render(<ArticleCard article={mockArticle} />);
  expect(screen.getByText('Fed Announces Rate Cut')).toBeInTheDocument();
});
```

## 🐛 Debugging Tests

### Backend Debugging

```bash
# Print output during tests
pytest -s tests/

# Enter debugger on failure
pytest --pdb tests/

# Only run failed tests
pytest --lf tests/

# Show local variables on failure
pytest -l tests/
```

### Frontend Debugging

```bash
# Debug mode
pnpm test --reporter=verbose

# Single test file
pnpm test components.test.tsx

# Update snapshots
pnpm test -u
```

## ⚡ Performance Testing

### Measure Test Execution Time

```bash
# Backend
pytest --durations=10 tests/  # Show 10 slowest tests

# Frontend
pnpm test --reporter=verbose  # Shows timing
```

### Performance Benchmarks

Backend targets:
- Unit tests: <100ms each
- Integration tests: <2s each
- Full suite: <30s

Frontend targets:
- Component tests: <50ms each
- Integration tests: <1s each
- Full suite: <10s

## 🔍 Common Issues & Solutions

### Issue: Database Locked

```bash
# Solution: Enable WAL mode
# Already handled in conftest.py
```

### Issue: OpenAI API Mocks Not Working

```python
# Ensure mock is imported before test
from unittest.mock import patch

@patch('openai.AsyncOpenAI')
def test_with_mock(mock_openai):
    ...
```

### Issue: Frontend Tests Can't Find Components

```typescript
// Ensure component path is correct
import { ArticleCard } from '@/components/ArticleCard';
```

### Issue: Docker Tests Timeout

```bash
# Increase timeout in test_container.sh
TEST_TIMEOUT=600  # 10 minutes
```

## 📈 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=app tests/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: pnpm install
      - run: pnpm test:coverage

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: ./tests/docker/test_container.sh
```

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Coverage >80%
- [ ] No flaky tests
- [ ] Performance benchmarks met
- [ ] Docker container tests passing
- [ ] No skipped critical tests
- [ ] Error handling tested
- [ ] Edge cases covered

## 🔄 Test Maintenance

### Regular Tasks

- Review and update mocks monthly
- Add tests for new features
- Remove obsolete tests
- Update fixtures as schema changes
- Refactor slow tests
- Document test patterns

### Test Quality Metrics

- Test readability: Can new developers understand them?
- Test isolation: Each test independent?
- Test speed: Running efficiently?
- Test coverage: Catching real bugs?

---

**Good testing practices lead to confident deployments! 🚀**
