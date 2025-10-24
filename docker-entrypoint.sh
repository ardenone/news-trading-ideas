#!/bin/bash
set -e

echo "=========================================="
echo "News Trading Ideas MVP - Starting..."
echo "=========================================="

# Check environment
echo "Checking environment..."

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY not set!"
fi

# Create data directory if it doesn't exist
mkdir -p /data

# Initialize database with Python (avoiding shell nesting)
echo "Initializing database..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

os.makedirs("/data", exist_ok=True)
conn = sqlite3.connect("/data/news_trading.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
print("Database initialized successfully")
PYTHON_SCRIPT

# Check database file
if [ -f "/data/news_trading.db" ]; then
    echo "Database file exists at /data/news_trading.db"
    ls -lh /data/news_trading.db
fi

# Display configuration
echo "----------------------------------------"
echo "Configuration:"
echo "  Environment: ${APP_ENV:-production}"
echo "  Log Level: ${LOG_LEVEL:-INFO}"
echo "  Database: ${DATABASE_URL:-sqlite:///data/news_trading.db}"
echo "  Port: 8000"
echo "----------------------------------------"

echo "Starting application server..."
echo "=========================================="

# Execute the main command (uvicorn)
exec "$@"
