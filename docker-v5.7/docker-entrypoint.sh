#!/bin/bash
set -e

# Load .env if exists (fallback for unset vars)
if [ -f /app/.env ]; then
  export $(grep -v '^#' /app/.env | xargs)
fi

# Path to secrets.env
SECRETS_FILE="/app/config/secrets.env"

# Generate secrets.env ONLY if it doesn't exist or is empty
if [ ! -f "$SECRETS_FILE" ] || [ ! -s "$SECRETS_FILE" ]; then
  echo "Generating $SECRETS_FILE from environment variables..."
  cat > "$SECRETS_FILE" << EOF
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
else
  echo "$SECRETS_FILE exists and is not empty - preserving admin updates."
fi

# Start atd for system restart functionality
atd &

# Execute the main container command
exec "$@"
