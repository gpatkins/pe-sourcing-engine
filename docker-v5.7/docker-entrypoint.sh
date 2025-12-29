#!/bin/bash
set -e

SECRETS_FILE="/app/config/secrets.env"

# Only generate if file does NOT exist or is empty
if [ ! -f "$SECRETS_FILE" ] || [ ! -s "$SECRETS_FILE" ]; then
  echo "Generating initial $SECRETS_FILE..."
  
  # Only write API keys if they are actually set (not empty, not "None")
  cat > "$SECRETS_FILE" << EOF
# Auto-generated on first start
# Update via Admin Dashboard > API Keys

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-pe_sourcing_db}
DB_USER=${DB_USER:-pe_sourcer}
DB_PASS=${DB_PASS:-changeme}

METABASE_URL=${METABASE_URL:-http://metabase:3000}
EOF

  # Only add API keys if they have real values (not empty, not "None")
  if [ -n "$GOOGLE_PLACES_API_KEY" ] && [ "$GOOGLE_PLACES_API_KEY" != "None" ]; then
    echo "GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}" >> "$SECRETS_FILE"
  else
    echo "GOOGLE_PLACES_API_KEY=" >> "$SECRETS_FILE"
  fi

  if [ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "None" ]; then
    echo "GEMINI_API_KEY=${GEMINI_API_KEY}" >> "$SECRETS_FILE"
  else
    echo "GEMINI_API_KEY=" >> "$SECRETS_FILE"
  fi

  if [ -n "$SERPER_API_KEY" ] && [ "$SERPER_API_KEY" != "None" ]; then
    echo "SERPER_API_KEY=${SERPER_API_KEY}" >> "$SECRETS_FILE"
  else
    echo "SERPER_API_KEY=" >> "$SECRETS_FILE"
  fi

  echo "✅ $SECRETS_FILE created"
else
  echo "✅ $SECRETS_FILE exists - preserving admin updates"
fi

# Start atd for scheduled tasks
atd 2>/dev/null &

exec "$@"
