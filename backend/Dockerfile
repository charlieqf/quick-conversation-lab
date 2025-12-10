# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (none needed for basic FastAPI, but good practice to have apt update)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run defaults to 8080, but we use $PORT env var)
# EXPOSE 8080

# Run the application
# Cloud Run injects the PORT environment variable, uvicorn needs to listen on it
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
