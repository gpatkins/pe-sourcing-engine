# PE Sourcing Engine v5.1 - Docker Image
# Multi-user SaaS platform with JWT authentication

# DOWNGRADED to 3.13 to fix SQLAlchemy 2.0.35 compatibility issue
FROM python:3.13-slim

LABEL maintainer="Gabriel Atkinson"
LABEL version="5.1"
LABEL description="PE Sourcing Engine - Automated Deal Origination Platform"

# System dependencies for PostgreSQL, XML parsing, and compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/config

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
