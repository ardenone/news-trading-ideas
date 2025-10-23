#!/bin/bash
# ============================================================================
# News Trading Ideas Platform - Docker Entrypoint Script
# ============================================================================
# This script runs on container startup to:
# 1. Validate environment variables
# 2. Initialize directories
# 3. Initialize database (if needed)
# 4. Start the application
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# 1. ENVIRONMENT VALIDATION
# ============================================================================
log_info "Validating environment variables..."

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    log_error "OPENAI_API_KEY is not set. Please set it in .env file."
    exit 1
fi

# Validate API key format (basic check)
if [[ ! $OPENAI_API_KEY =~ ^sk- ]]; then
    log_warn "OPENAI_API_KEY may be invalid (should start with 'sk-')"
fi

log_info "Environment variables validated successfully"

# ============================================================================
# 2. DIRECTORY INITIALIZATION
# ============================================================================
log_info "Initializing directories..."

# Create data directory if it doesn't exist
if [ ! -d "/data" ]; then
    log_info "Creating /data directory..."
    mkdir -p /data
fi

# Create logs directory if it doesn't exist
if [ ! -d "/app/logs" ]; then
    log_info "Creating /app/logs directory..."
    mkdir -p /app/logs
fi

# Create backups directory
if [ ! -d "/data/backups" ]; then
    log_info "Creating /data/backups directory..."
    mkdir -p /data/backups
fi

log_info "Directories initialized successfully"

# ============================================================================
# 3. DATABASE INITIALIZATION
# ============================================================================
DATABASE_PATH="/data/app.db"

if [ ! -f "$DATABASE_PATH" ]; then
    log_info "Database not found at $DATABASE_PATH"
    log_info "Initializing new SQLite database..."

    # Check if schema file exists
    SCHEMA_FILE="/app/db/schema.sql"
    if [ ! -f "$SCHEMA_FILE" ]; then
        log_error "Database schema file not found at $SCHEMA_FILE"
        exit 1
    fi

    # Create database from schema
    sqlite3 "$DATABASE_PATH" < "$SCHEMA_FILE"

    # Enable WAL mode for better concurrency
    sqlite3 "$DATABASE_PATH" "PRAGMA journal_mode=WAL;"
    sqlite3 "$DATABASE_PATH" "PRAGMA synchronous=NORMAL;"
    sqlite3 "$DATABASE_PATH" "PRAGMA cache_size=-64000;"
    sqlite3 "$DATABASE_PATH" "PRAGMA foreign_keys=ON;"

    log_info "Database initialized successfully"
else
    log_info "Existing database found at $DATABASE_PATH"

    # Verify database integrity
    INTEGRITY_CHECK=$(sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check;")
    if [ "$INTEGRITY_CHECK" != "ok" ]; then
        log_error "Database integrity check failed: $INTEGRITY_CHECK"
        exit 1
    fi

    # Verify WAL mode is enabled
    JOURNAL_MODE=$(sqlite3 "$DATABASE_PATH" "PRAGMA journal_mode;")
    if [ "$JOURNAL_MODE" != "wal" ]; then
        log_warn "Database not in WAL mode. Enabling WAL mode..."
        sqlite3 "$DATABASE_PATH" "PRAGMA journal_mode=WAL;"
    fi

    log_info "Database validation completed"
fi

# ============================================================================
# 4. DATABASE MIGRATION (Optional - if using Alembic)
# ============================================================================
if [ -f "/app/alembic.ini" ]; then
    log_info "Running database migrations..."

    # Check if we're in a clean state
    if python -m alembic current &> /dev/null; then
        python -m alembic upgrade head
        log_info "Database migrations completed"
    else
        log_warn "Alembic not configured or no migrations found"
    fi
fi

# ============================================================================
# 5. INITIAL DATA SEEDING (Optional)
# ============================================================================
# Check if this is first startup by looking for system_metadata
ROW_COUNT=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM rss_feeds;" 2>/dev/null || echo "0")

if [ "$ROW_COUNT" -eq "0" ]; then
    log_info "No RSS feeds found. This appears to be first startup."
    log_info "You can add feeds via the API at http://localhost:8000/docs"
    log_info "Or create a seed data script in /app/db/seed.py"
fi

# ============================================================================
# 6. LOGGING SETUP
# ============================================================================
log_info "Setting up logging..."

# Create log files with proper permissions
touch /app/logs/app.log
touch /app/logs/ingestion.log
touch /app/logs/api.log
touch /app/logs/ai.log

log_info "Logging configured"

# ============================================================================
# 7. CONNECTIVITY CHECKS
# ============================================================================
log_info "Checking external service connectivity..."

# Test OpenAI API connectivity (simple check)
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models)

    if [ "$HTTP_CODE" -eq "200" ]; then
        log_info "OpenAI API connectivity verified"
    else
        log_warn "OpenAI API returned HTTP $HTTP_CODE (may be rate limit or key issue)"
    fi
else
    log_warn "curl not available, skipping connectivity check"
fi

# ============================================================================
# 8. SCHEDULED TASKS SETUP (Optional - if using cron in container)
# ============================================================================
# Uncomment if you want to run backup cron inside container
# log_info "Setting up scheduled tasks..."
#
# # Create crontab for daily backups at 2 AM UTC
# cat > /tmp/crontab << EOF
# 0 2 * * * /app/scripts/backup.sh >> /app/logs/backup.log 2>&1
# EOF
#
# crontab /tmp/crontab
# log_info "Scheduled tasks configured"

# ============================================================================
# 9. STARTUP INFORMATION
# ============================================================================
log_info "=========================================="
log_info "News Trading Ideas Platform"
log_info "=========================================="
log_info "Database: $DATABASE_PATH"
log_info "Logs: /app/logs/"
log_info "API Port: ${API_PORT:-8000}"
log_info "Environment: ${APP_ENV:-production}"
log_info "Log Level: ${LOG_LEVEL:-INFO}"
log_info "=========================================="
log_info "Starting application..."
log_info "=========================================="

# ============================================================================
# 10. START APPLICATION
# ============================================================================
# Execute the command passed to the container (defaults to uvicorn)
exec "$@"
