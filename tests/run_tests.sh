#!/bin/bash

###############################################################################
# Comprehensive Test Runner for News Trading Ideas MVP
# Runs backend, frontend, and Docker tests with reporting
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="/home/jarden/news-trading-ideas"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TESTS_DIR="$PROJECT_ROOT/tests"

# Results tracking
BACKEND_PASSED=0
FRONTEND_PASSED=0
DOCKER_PASSED=0

###############################################################################
# Helper Functions
###############################################################################

log_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

###############################################################################
# Pre-Flight Checks
###############################################################################

log_header "Pre-Flight Checks"

cd "$PROJECT_ROOT"

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.11+"
    exit 1
else
    log_info "Python: $(python3 --version)"
fi

# Check Poetry
if ! command -v poetry &> /dev/null; then
    log_warn "Poetry not found. Installing..."
    pip install poetry
fi

# Check Node/pnpm
if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Frontend tests will be skipped."
else
    log_info "Node: $(node --version)"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    log_warn "Docker not found. Docker tests will be skipped."
else
    log_info "Docker: $(docker --version)"
fi

###############################################################################
# Backend Tests (pytest)
###############################################################################

log_header "Backend Tests (pytest)"

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"

    # Install dependencies
    log_info "Installing backend dependencies..."
    if [ -f "pyproject.toml" ]; then
        poetry install --with dev --quiet
    else
        log_warn "No pyproject.toml found. Creating minimal test environment..."
        pip install pytest pytest-asyncio pytest-cov pytest-timeout --quiet
    fi

    # Run tests
    log_info "Running backend tests..."
    if [ -f "pyproject.toml" ]; then
        if poetry run pytest "$TESTS_DIR/backend" -v --tb=short; then
            BACKEND_PASSED=1
            log_info "✓ Backend tests PASSED"
        else
            log_error "✗ Backend tests FAILED"
        fi

        # Generate coverage report
        log_info "Generating coverage report..."
        poetry run pytest "$TESTS_DIR/backend" --cov=app --cov-report=html --cov-report=term-missing || true
    else
        if pytest "$TESTS_DIR/backend" -v --tb=short; then
            BACKEND_PASSED=1
            log_info "✓ Backend tests PASSED"
        else
            log_error "✗ Backend tests FAILED"
        fi
    fi

    cd "$PROJECT_ROOT"
else
    log_warn "Backend directory not found. Skipping backend tests."
fi

###############################################################################
# Frontend Tests (Vitest)
###############################################################################

log_header "Frontend Tests (Vitest)"

if [ -d "$FRONTEND_DIR" ] && command -v node &> /dev/null; then
    cd "$FRONTEND_DIR"

    # Check for package.json
    if [ -f "package.json" ]; then
        # Install dependencies
        log_info "Installing frontend dependencies..."
        if command -v pnpm &> /dev/null; then
            pnpm install --silent
        else
            npm install --silent
        fi

        # Run tests
        log_info "Running frontend tests..."
        if command -v pnpm &> /dev/null; then
            if pnpm test; then
                FRONTEND_PASSED=1
                log_info "✓ Frontend tests PASSED"
            else
                log_error "✗ Frontend tests FAILED"
            fi
        else
            if npm test; then
                FRONTEND_PASSED=1
                log_info "✓ Frontend tests PASSED"
            else
                log_error "✗ Frontend tests FAILED"
            fi
        fi
    else
        log_warn "No package.json found. Skipping frontend tests."
    fi

    cd "$PROJECT_ROOT"
else
    log_warn "Frontend directory not found or Node.js not installed. Skipping frontend tests."
fi

###############################################################################
# Docker Integration Tests
###############################################################################

log_header "Docker Integration Tests"

if command -v docker &> /dev/null; then
    cd "$PROJECT_ROOT"

    if [ -f "$TESTS_DIR/docker/test_container.sh" ]; then
        # Make executable
        chmod +x "$TESTS_DIR/docker/test_container.sh"

        # Run Docker tests
        log_info "Running Docker integration tests..."
        if "$TESTS_DIR/docker/test_container.sh"; then
            DOCKER_PASSED=1
            log_info "✓ Docker tests PASSED"
        else
            log_error "✗ Docker tests FAILED"
        fi
    else
        log_warn "Docker test script not found. Skipping Docker tests."
    fi
else
    log_warn "Docker not installed. Skipping Docker tests."
fi

###############################################################################
# Test Results Summary
###############################################################################

log_header "Test Results Summary"

echo -e "\n📊 ${BLUE}Test Suite Results:${NC}\n"

if [ $BACKEND_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Backend Tests (pytest)"
else
    echo -e "  ${RED}✗${NC} Backend Tests (pytest)"
fi

if [ $FRONTEND_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Frontend Tests (Vitest)"
else
    echo -e "  ${RED}✗${NC} Frontend Tests (Vitest)"
fi

if [ $DOCKER_PASSED -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Docker Integration Tests"
else
    echo -e "  ${RED}✗${NC} Docker Integration Tests"
fi

echo ""

# Overall result
TOTAL_SUITES=3
PASSED_SUITES=$((BACKEND_PASSED + FRONTEND_PASSED + DOCKER_PASSED))

echo -e "${BLUE}Overall:${NC} $PASSED_SUITES/$TOTAL_SUITES test suites passed\n"

# Coverage report location
if [ -f "$BACKEND_DIR/htmlcov/index.html" ]; then
    echo -e "${BLUE}Coverage Report:${NC} $BACKEND_DIR/htmlcov/index.html\n"
fi

###############################################################################
# Recommendations
###############################################################################

if [ $PASSED_SUITES -lt $TOTAL_SUITES ]; then
    log_header "Recommendations"

    if [ $BACKEND_PASSED -eq 0 ]; then
        echo -e "${YELLOW}Backend:${NC} Review pytest output above for failure details"
        echo -e "  Run: ${BLUE}cd backend && poetry run pytest tests/backend -v${NC}"
    fi

    if [ $FRONTEND_PASSED -eq 0 ]; then
        echo -e "${YELLOW}Frontend:${NC} Review test output for component/API client issues"
        echo -e "  Run: ${BLUE}cd frontend && pnpm test${NC}"
    fi

    if [ $DOCKER_PASSED -eq 0 ]; then
        echo -e "${YELLOW}Docker:${NC} Check Dockerfile and container logs"
        echo -e "  Run: ${BLUE}./tests/docker/test_container.sh${NC}"
    fi

    echo ""
fi

###############################################################################
# Exit Status
###############################################################################

if [ $PASSED_SUITES -eq $TOTAL_SUITES ]; then
    log_info "All test suites passed! 🎉"
    exit 0
else
    log_error "Some test suites failed. Please review output above."
    exit 1
fi
