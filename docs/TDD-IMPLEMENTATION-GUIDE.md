# Test-Driven Development Implementation Guide

## 🎯 Overview

This guide provides a comprehensive TDD workflow for the News Trading Ideas MVP platform. All tests have been created following industry best practices with >80% coverage targets.

## 📁 Test Suite Structure

### Complete Test Organization

```
tests/
├── backend/                    # Backend Python tests (pytest)
│   ├── conftest.py            # Fixtures and test configuration
│   ├── test_rss_ingestion.py  # RSS parsing, deduplication
│   ├── test_openai_integration.py  # OpenAI API mocking
│   ├── test_database.py       # SQLite CRUD, indexes, triggers
│   ├── test_clustering.py     # DBSCAN clustering algorithms
│   ├── test_trading_ideas.py  # Trading ideas generation
│   └── test_api_endpoints.py  # FastAPI route testing
├── frontend/                   # Frontend TypeScript tests (Vitest)
│   ├── components.test.tsx    # React component tests
│   └── api-client.test.ts     # API client integration
├── docker/                     # Docker integration tests
│   └── test_container.sh      # Container build/run/health
├── pytest.ini                  # Pytest configuration
├── run_tests.sh               # Unified test runner
└── README.md                   # Test documentation
```

## 🚀 Quick Start

### 1. Run All Tests

```bash
# From project root
./tests/run_tests.sh
```

This script runs:
- Backend tests (pytest)
- Frontend tests (Vitest)
- Docker integration tests

### 2. Run Backend Tests Only

```bash
cd backend
poetry install --with dev
poetry run pytest tests/backend -v

# With coverage
poetry run pytest tests/backend --cov=app --cov-report=html
```

### 3. Run Frontend Tests Only

```bash
cd frontend
pnpm install
pnpm test

# Watch mode
pnpm test:watch
```

### 4. Run Docker Tests Only

```bash
./tests/docker/test_container.sh
```

## 🔄 Iterative TDD Workflow

### Phase 1: Initial Setup & Discovery

```bash
# 1. Review specifications
cat docs/SPECIFICATION.md
cat architecture/mvp-plan.md

# 2. Understand database schema
cat architecture/database-schema.sql

# 3. Check existing tests
ls tests/backend/
```

### Phase 2: Build → Run → Review → Fix Loop

```bash
# ITERATION 1: Build Docker Container

# Build
docker build -t news-trading-ideas:test .

# Run
docker run -d --name test-container -p 8000:8000 --env-file .env news-trading-ideas:test

# Test
./tests/docker/test_container.sh

# Review Logs
docker logs test-container

# Identify Issues
# - Missing dependencies?
# - Configuration errors?
# - Database schema issues?

# Fix Issues
# - Update Dockerfile
# - Fix application code
# - Update configuration

# Cleanup
docker stop test-container && docker rm test-container

# REPEAT until container runs successfully
```

### Phase 3: Backend Test Execution

```bash
# ITERATION 2: Backend Tests

# Run specific test modules
pytest tests/backend/test_database.py -v

# Identify failures
# - Database schema mismatch?
# - Missing tables/columns?
# - Index creation issues?

# Fix database schema
# - Update database-schema.sql
# - Run migrations

# Re-run tests
pytest tests/backend/test_database.py -v

# REPEAT for each test module
```

### Phase 4: Integration Testing

```bash
# ITERATION 3: API Integration

# Start backend
cd backend
poetry run uvicorn app.main:app --reload

# Run API tests
pytest tests/backend/test_api_endpoints.py -v

# Identify issues
# - Missing endpoints?
# - Validation errors?
# - Authentication issues?

# Fix API code
# - Implement missing routes
# - Add validation
# - Configure CORS

# Re-run tests
pytest tests/backend/test_api_endpoints.py -v
```

### Phase 5: Full System Integration

```bash
# ITERATION 4: Complete System

# Build full Docker stack
docker-compose up -d

# Wait for health
curl http://localhost:8000/health

# Run all tests
./tests/run_tests.sh

# Review results
# - Backend: PASSED/FAILED
# - Frontend: PASSED/FAILED
# - Docker: PASSED/FAILED

# Document issues
# Create ISSUES.md with all failures

# Fix highest priority issues first
# Re-test after each fix

# REPEAT until all tests pass
```

## 📊 Test Coverage Targets

### Backend Coverage

| Component | Target | Current | Priority |
|-----------|--------|---------|----------|
| Models | >90% | TBD | High |
| Services | >85% | TBD | High |
| API Endpoints | >80% | TBD | High |
| Utilities | >75% | TBD | Medium |
| Database Queries | >75% | TBD | Medium |

### Frontend Coverage

| Component | Target | Current | Priority |
|-----------|--------|---------|----------|
| Components | >80% | TBD | High |
| API Client | >90% | TBD | High |
| Hooks | >85% | TBD | Medium |
| Utilities | >80% | TBD | Medium |

## 🧪 Test Categories

### 1. RSS Ingestion Tests (test_rss_ingestion.py)

**Test Classes:**
- `TestRSSFeedParsing` - Feed parsing and validation
- `TestArticleDeduplication` - Content hash deduplication
- `TestArticleStorage` - Database storage
- `TestFeedManagement` - Feed CRUD operations
- `TestErrorHandling` - Error scenarios
- `TestPerformance` - Bulk operations

**Key Tests:**
- Parse valid RSS feeds
- Handle malformed XML
- Detect duplicate articles
- Store articles with all fields
- Track processing status

### 2. OpenAI Integration Tests (test_openai_integration.py)

**Test Classes:**
- `TestEmbeddingsGeneration` - Embeddings creation
- `TestClustering` - Similarity search
- `TestClusterSummarization` - GPT summaries
- `TestCostTracking` - API cost monitoring
- `TestNoViableTradingIdeas` - Empty state handling

**Key Tests:**
- Generate embeddings (mocked)
- Batch embedding creation
- Handle rate limiting
- Exponential backoff
- Calculate cosine similarity
- DBSCAN clustering
- Filter low-confidence ideas

### 3. Database Tests (test_database.py)

**Test Classes:**
- `TestDatabaseSchema` - Schema validation
- `TestCRUDOperations` - Create/Read/Update/Delete
- `TestArticleOperations` - Article-specific logic
- `TestNewsEventsAndClusters` - Clustering operations
- `TestTradingIdeas` - Trading ideas storage
- `TestDatabaseViews` - View queries
- `TestIndexPerformance` - Index effectiveness
- `TestDataRetention` - Cleanup logic

**Key Tests:**
- All tables exist
- Foreign keys work
- Triggers fire correctly
- Views return data
- Indexes improve performance

### 4. Clustering Tests (test_clustering.py)

**Test Classes:**
- `TestDBSCANClustering` - DBSCAN algorithm
- `TestSimilarityMetrics` - Similarity calculations
- `TestClusterQuality` - Silhouette scores
- `TestClusteringWorkflow` - End-to-end workflow
- `TestClusterMetadata` - Impact scores
- `TestEdgeCases` - Edge case handling
- `TestPerformance` - Performance benchmarks

**Key Tests:**
- Cluster similar vectors
- Detect noise points
- Calculate cosine similarity
- Measure cluster cohesion
- Handle empty embeddings
- Performance on 1000+ articles

### 5. Trading Ideas Tests (test_trading_ideas.py)

**Test Classes:**
- `TestTradingIdeaGeneration` - Idea generation
- `TestTopEventSelection` - Top 10 selection
- `TestIdeaDuplication` - Duplicate prevention
- `TestStrategyValidation` - Strategy validation
- `TestIdeaExpiration` - Expiration logic
- `TestIdeaQualityScoring` - Confidence scoring
- `TestNoViableIdeasScenario` - Empty state handling

**Key Tests:**
- Generate trading ideas
- Filter low confidence (<6.0)
- Select top 10 events by impact
- Prevent duplicates
- Handle no viable ideas scenario

### 6. API Endpoint Tests (test_api_endpoints.py)

**Test Classes:**
- `TestHealthEndpoint` - Health checks
- `TestFeedEndpoints` - Feed CRUD
- `TestArticleEndpoints` - Article operations
- `TestClusterEndpoints` - Cluster operations
- `TestTradingIdeasEndpoints` - Ideas operations
- `TestErrorHandling` - HTTP errors
- `TestPagination` - Pagination support
- `TestEmptyStates` - Empty list handling
- `TestPerformance` - Response time requirements

**Key Tests:**
- All endpoints return correct status codes
- Pagination works
- Filters work
- Error handling is graceful
- Response time <2s (p95)

### 7. Docker Integration Tests (test_container.sh)

**Test Phases:**
1. Docker build succeeds
2. Container starts
3. Health check passes
4. API endpoints respond
5. No critical errors in logs
6. Volume mounts work
7. Environment variables loaded
8. Database initializes
9. Resource usage reasonable
10. Container restarts successfully

## 🐛 Common Issues & Fixes

### Issue 1: Backend Tests Fail - "No such table"

**Cause:** Database schema not applied

**Fix:**
```bash
cd backend
# Ensure schema SQL file is used in conftest.py
# Verify schema path in conftest.py line ~37
pytest tests/backend/test_database.py -v
```

### Issue 2: OpenAI Tests Fail - "Module not found"

**Cause:** Missing openai package or incorrect mocking

**Fix:**
```bash
poetry add openai
# Check mock imports in conftest.py
# Verify patch paths match actual imports
```

### Issue 3: Docker Tests Timeout

**Cause:** Application not starting

**Fix:**
```bash
# Check Dockerfile CMD
# Verify health endpoint exists
# Review docker logs
docker logs test-container
```

### Issue 4: Frontend Tests Can't Find Components

**Cause:** Components not yet implemented

**Fix:**
```typescript
// Create minimal component stubs
// Update import paths to match structure
// Use placeholder tests until implementation
```

### Issue 5: Coverage Report Empty

**Cause:** No app/ directory exists yet

**Fix:**
```bash
# Create minimal app structure
mkdir -p backend/app
touch backend/app/__init__.py
# Re-run with coverage
pytest tests/backend --cov=app
```

## 📈 Progress Tracking

### Test Execution Log Template

```markdown
## Test Iteration Log

### Iteration 1: 2025-10-22 22:00
- **Built:** Docker image
- **Tests Run:** Docker container tests
- **Result:** ❌ FAILED
- **Issues:**
  - Missing Dockerfile
  - No app structure
- **Fixes Applied:**
  - Created minimal Dockerfile
  - Added health endpoint stub
- **Next Steps:**
  - Implement FastAPI app structure
  - Add database connection

### Iteration 2: 2025-10-22 23:00
- **Built:** Docker image (v2)
- **Tests Run:** Backend + Docker tests
- **Result:** ⚠️ PARTIAL
- **Passed:** 45/100 tests
- **Failed:** 55 tests
- **Issues:**
  - Database schema incomplete
  - Missing API endpoints
- **Fixes Applied:**
  - Applied full database schema
  - Implemented /health endpoint
- **Next Steps:**
  - Implement feed endpoints
  - Add article endpoints
```

## 🎯 Success Criteria

### Phase 1: Basic Infrastructure (Week 1)
- [x] All test files created
- [ ] Database schema applied
- [ ] Docker container builds successfully
- [ ] Health endpoint responds

### Phase 2: Core Features (Week 2)
- [ ] RSS ingestion tests pass
- [ ] Database tests pass
- [ ] API endpoints implemented
- [ ] 50%+ backend tests passing

### Phase 3: AI Integration (Week 3)
- [ ] OpenAI mocking works
- [ ] Clustering tests pass
- [ ] Trading ideas tests pass
- [ ] 75%+ backend tests passing

### Phase 4: Complete System (Week 4)
- [ ] All backend tests pass
- [ ] Frontend components implemented
- [ ] Frontend tests pass
- [ ] Docker tests pass
- [ ] >80% overall coverage

## 📝 Documentation Checklist

For each iteration:
- [ ] Log test results
- [ ] Document failures
- [ ] Record fixes applied
- [ ] Update coverage metrics
- [ ] Note performance benchmarks
- [ ] Identify remaining work

## 🔗 Related Documentation

- [Test README](tests/README.md) - Detailed test execution guide
- [Architecture Docs](architecture/) - System design reference
- [Executive Summary](EXECUTIVE-SUMMARY.md) - Project overview
- [Quick Start Guide](QUICK-START.md) - Setup instructions

## ✅ Final Checklist

Before declaring MVP complete:

### Backend
- [ ] All pytest tests passing
- [ ] Coverage >80%
- [ ] No skipped critical tests
- [ ] Performance benchmarks met
- [ ] Error handling comprehensive

### Frontend
- [ ] All component tests passing
- [ ] API client tests passing
- [ ] Coverage >80%
- [ ] No console errors

### Docker
- [ ] Container builds successfully
- [ ] All services start
- [ ] Health checks pass
- [ ] API responds correctly
- [ ] No critical log errors

### Integration
- [ ] End-to-end workflows work
- [ ] Database persists data
- [ ] RSS ingestion functional
- [ ] AI processing works
- [ ] Trading ideas generate

---

**TDD Principle:** Write tests first, code second. Let tests guide your implementation! 🚀
