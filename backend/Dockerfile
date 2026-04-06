FROM python:3.12-slim

# Install system deps for Playwright + asyncpg
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (skip fonts that don't exist in slim)
RUN playwright install-deps chromium 2>/dev/null || true && playwright install chromium

# Copy source
COPY . .

# Default: run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
