#!/bin/bash
set -e

echo "=========================================="
echo "News Trading Ideas MVP - Starting..."
echo "=========================================="

# Wait for any dependencies (if needed)
echo "Checking environment..."

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY not set!"
fi

if [ -z "$NEWS_API_KEY" ]; then
    echo "WARNING: NEWS_API_KEY not set!"
fi

# Create data directory if it doesn't exist
mkdir -p /app/data

# Initialize database
echo "Initializing database..."
cd /app/backend

# Run database migrations or initialization
python -c "
import sys
sys.path.insert(0, '/app/backend')
try:
    from database import init_db
    init_db()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization: {e}')
"

# Check database file
if [ -f "/app/data/news_trading.db" ]; then
    echo "Database file exists at /app/data/news_trading.db"
    ls -lh /app/data/news_trading.db
else
    echo "Database file will be created on first run"
fi

# Display configuration
echo "----------------------------------------"
echo "Configuration:"
echo "  Environment: ${ENVIRONMENT:-production}"
echo "  Log Level: ${LOG_LEVEL:-info}"
echo "  Database: ${DATABASE_URL:-sqlite:///data/news_trading.db}"
echo "  Port: 8000"
echo "----------------------------------------"

# Health check on startup
echo "Starting application server..."
echo "=========================================="

# Execute the main command
exec "$@"
