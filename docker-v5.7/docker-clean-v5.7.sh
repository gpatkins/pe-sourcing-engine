#!/bin/bash
# PE Sourcing Engine v5.7 - Docker Cleanup Script
# Runs INSIDE the app container (no sudo needed)

echo "--- 🧹 Docker Container Cleanup ---"

echo "1. Clearing Python bytecode cache..."
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /app -type f -name "*.pyc" -delete 2>/dev/null
echo "   ✓ Python cache cleared"

echo "2. Clearing application logs older than 7 days..."
find /app/logs -type f -name "*.log" -mtime +7 -delete 2>/dev/null
echo "   ✓ Old logs cleared"

echo "3. Checking disk usage..."
df -h /app 2>/dev/null || echo "   (disk stats not available)"

echo ""
echo "--- ✅ Container Cleanup Complete ---"
echo "Note: Database vacuum and system cache should be done from host"
