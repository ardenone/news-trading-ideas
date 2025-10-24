#!/bin/bash
set -e

echo "Starting News Trading Ideas MVP..."

# Initialize database
echo "Initializing database..."
cd /app
python -c "from backend.database import init_db; init_db()"

echo "Database initialized successfully"

# Execute CMD
exec "$@"
