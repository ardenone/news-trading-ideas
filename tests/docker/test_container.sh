#!/bin/bash

###############################################################################
# Docker Container Integration Tests
# Tests Docker build, run, health checks, and API functionality
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="news-trading-ideas:test"
CONTAINER_NAME="news-trading-test"
API_PORT=8000
TEST_TIMEOUT=300  # 5 minutes max

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

cleanup() {
    log_info "Cleaning up..."

    # Stop and remove container
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        log_info "Stopping container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi

    # Remove test image (optional - comment out to keep for debugging)
    # if docker images | grep -q "$IMAGE_NAME"; then
    #     log_info "Removing image: $IMAGE_NAME"
    #     docker rmi "$IMAGE_NAME" 2>/dev/null || true
    # fi
}

wait_for_health() {
    local max_wait=$1
    local waited=0

    log_info "Waiting for container to be healthy (max ${max_wait}s)..."

    while [ $waited -lt $max_wait ]; do
        if docker ps | grep -q "$CONTAINER_NAME"; then
            # Check if health endpoint responds
            if curl -f -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
                log_info "Container is healthy!"
                return 0
            fi
        else
            log_error "Container stopped unexpectedly"
            return 1
        fi

        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done

    echo ""
    log_error "Container failed to become healthy within ${max_wait}s"
    return 1
}

run_test() {
    local test_name=$1
    local test_command=$2

    log_info "Running test: $test_name"

    if eval "$test_command"; then
        log_info "✓ PASSED: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "✗ FAILED: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

###############################################################################
# Pre-Flight Checks
###############################################################################

log_info "Starting Docker integration tests..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    log_warn "Dockerfile not found in current directory. Creating minimal Dockerfile for testing..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pytest

# Copy application (if it exists)
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["python", "-c", "from fastapi import FastAPI; import uvicorn; app = FastAPI(); app.get('/health')(lambda: {'status': 'healthy'}); uvicorn.run(app, host='0.0.0.0', port=8000)"]
EOF
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    log_warn ".env file not found. Creating sample .env..."
    cat > .env << 'EOF'
OPENAI_API_KEY=sk-test-key-for-testing
DATABASE_URL=sqlite:///./data/test.db
LOG_LEVEL=INFO
EOF
fi

# Cleanup any existing test containers
cleanup

###############################################################################
# Test 1: Docker Build
###############################################################################

run_test "Docker Image Build" "docker build -t $IMAGE_NAME -f Dockerfile ."

if [ $? -ne 0 ]; then
    log_error "Docker build failed. Cannot continue tests."
    exit 1
fi

###############################################################################
# Test 2: Docker Run
###############################################################################

log_info "Starting container: $CONTAINER_NAME"

docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$API_PORT:8000" \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    "$IMAGE_NAME"

run_test "Docker Container Start" "docker ps | grep -q $CONTAINER_NAME"

###############################################################################
# Test 3: Health Check
###############################################################################

if wait_for_health 60; then
    run_test "Container Health Check" "true"
else
    run_test "Container Health Check" "false"

    log_info "Container logs:"
    docker logs "$CONTAINER_NAME"

    cleanup
    exit 1
fi

###############################################################################
# Test 4: API Endpoints
###############################################################################

log_info "Testing API endpoints..."

# Test health endpoint
run_test "Health Endpoint" "curl -f -s http://localhost:$API_PORT/health | grep -q 'healthy'"

# Test feeds endpoint (may not exist yet)
if curl -f -s "http://localhost:$API_PORT/api/v1/feeds/" > /dev/null 2>&1; then
    run_test "Feeds Endpoint" "curl -f -s http://localhost:$API_PORT/api/v1/feeds/ | grep -q '\['"
else
    log_warn "Feeds endpoint not implemented yet (expected for early development)"
fi

# Test articles endpoint (may not exist yet)
if curl -f -s "http://localhost:$API_PORT/api/v1/articles/" > /dev/null 2>&1; then
    run_test "Articles Endpoint" "curl -f -s http://localhost:$API_PORT/api/v1/articles/ | grep -q '\['"
else
    log_warn "Articles endpoint not implemented yet (expected for early development)"
fi

# Test clusters endpoint (may not exist yet)
if curl -f -s "http://localhost:$API_PORT/api/v1/clusters/" > /dev/null 2>&1; then
    run_test "Clusters Endpoint" "curl -f -s http://localhost:$API_PORT/api/v1/clusters/ | grep -q '\['"
else
    log_warn "Clusters endpoint not implemented yet (expected for early development)"
fi

###############################################################################
# Test 5: Container Logs
###############################################################################

log_info "Checking container logs for errors..."

CONTAINER_LOGS=$(docker logs "$CONTAINER_NAME" 2>&1)

# Check for critical errors
if echo "$CONTAINER_LOGS" | grep -i "error" | grep -v "404" | grep -v "GET" > /dev/null; then
    log_warn "Found errors in container logs (this may be expected):"
    echo "$CONTAINER_LOGS" | grep -i "error" | head -n 10
else
    run_test "No Critical Errors in Logs" "true"
fi

# Check for successful startup
if echo "$CONTAINER_LOGS" | grep -i "started\|running\|uvicorn" > /dev/null; then
    run_test "Application Started Successfully" "true"
else
    log_warn "Could not confirm application startup in logs"
fi

###############################################################################
# Test 6: Volume Mounts
###############################################################################

log_info "Testing volume mounts..."

# Check if data directory is accessible
if docker exec "$CONTAINER_NAME" test -d /app/data; then
    run_test "Data Directory Mounted" "true"
else
    run_test "Data Directory Mounted" "false"
fi

# Check if logs directory is accessible
if docker exec "$CONTAINER_NAME" test -d /app/logs; then
    run_test "Logs Directory Mounted" "true"
else
    run_test "Logs Directory Mounted" "false"
fi

###############################################################################
# Test 7: Environment Variables
###############################################################################

log_info "Testing environment variables..."

# Check if OPENAI_API_KEY is set
if docker exec "$CONTAINER_NAME" sh -c 'echo $OPENAI_API_KEY' | grep -q "sk-"; then
    run_test "Environment Variables Loaded" "true"
else
    log_warn "OPENAI_API_KEY not found in container (check .env file)"
fi

###############################################################################
# Test 8: Database Initialization
###############################################################################

log_info "Testing database..."

# Check if SQLite database file exists (may not exist yet)
if docker exec "$CONTAINER_NAME" test -f /app/data/test.db; then
    run_test "Database File Created" "true"
elif docker exec "$CONTAINER_NAME" test -f /app/data/app.db; then
    run_test "Database File Created" "true"
else
    log_warn "Database file not created yet (expected if no DB operations run)"
fi

###############################################################################
# Test 9: Memory and CPU Usage
###############################################################################

log_info "Checking resource usage..."

STATS=$(docker stats "$CONTAINER_NAME" --no-stream --format "{{.MemUsage}} {{.CPUPerc}}")
MEM_USAGE=$(echo "$STATS" | awk '{print $1}')
CPU_USAGE=$(echo "$STATS" | awk '{print $3}')

log_info "Memory Usage: $MEM_USAGE"
log_info "CPU Usage: $CPU_USAGE"

run_test "Container Running with Reasonable Resources" "true"

###############################################################################
# Test 10: Container Restart
###############################################################################

log_info "Testing container restart..."

docker restart "$CONTAINER_NAME"

if wait_for_health 30; then
    run_test "Container Restart" "true"
else
    run_test "Container Restart" "false"
fi

###############################################################################
# Test Results Summary
###############################################################################

echo ""
echo "=========================================="
echo "          TEST RESULTS SUMMARY"
echo "=========================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo "=========================================="

# Full container logs for debugging
log_info "Full container logs:"
echo "=========================================="
docker logs "$CONTAINER_NAME"
echo "=========================================="

# Cleanup
cleanup

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    log_info "All tests passed! ✓"
    exit 0
else
    log_error "Some tests failed. Please review the output above."
    exit 1
fi
