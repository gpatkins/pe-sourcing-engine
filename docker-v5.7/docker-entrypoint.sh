#!/bin/bash
set -e

# Generate secrets.env from environment variables
# This allows admin panel to read/write API keys while keeping DB_HOST=db
cat > /app/config/secrets.env << EOF
# Auto-generated from Docker environment variables
# Admin panel updates to API keys will persist in this file

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-pe_sourcing_db}
DB_USER=${DB_USER:-pe_sourcer}
DB_PASS=${DB_PASS:-changeme}

GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY:-}
GOOGLE_GEMINI_API_KEY=${GOOGLE_GEMINI_API_KEY:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}
SERPER_API_KEY=${SERPER_API_KEY:-}

METABASE_URL=${METABASE_URL:-http://metabase:3000}
EOF

echo "Generated /app/config/secrets.env for application use"

# Start atd for system restart functionality
atd &

# Execute the main container command
exec "$@"
