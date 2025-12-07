# 1. Base Image: Lightweight Linux with Python 3.11
FROM python:3.11-slim

# 2. System Dependencies: Required for Postgres (psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup App Directory
WORKDIR /app

# 4. Install Python Dependencies (Cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the Application Code
COPY . .

# 6. Open Port 8000
EXPOSE 8000

# 7. Start the Dashboard
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
