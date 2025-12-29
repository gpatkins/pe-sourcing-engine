#!/bin/bash
set -e

# Path to secrets.env
SECRETS_FILE="/app/config/secrets.env"

# Only generate if file does NOT exist or is empty
if [ ! -f "$SECRETS_FILE" ] || [ ! -s "$SECRETS_FILE" ]; then
  echo "Generating initial $SECRETS_FILE from environment variables..."
  cat > "$SECRETS_FILE" << EOF
# Auto-generated from Docker environment variables on first start
# Can be updated via Admin dashboard after initial setup

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-pe_sourcing_db}
DB_USER=${DB_USER:-pe_sourcer}
DB_PASS=${DB_PASS:-changeme}

GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}
SERPER_API_KEY=${SERPER_API_KEY:-}

METABASE_URL=${METABASE_URL:-http://metabase:3000}
EOF
  echo "✅ $SECRETS_FILE created"
else
  echo "✅ $SECRETS_FILE already exists - preserving existing content"
fi

# Start atd for scheduled tasks (e.g. restarts)
atd 2>/dev/null &

# Execute the main application
exec "$@"
