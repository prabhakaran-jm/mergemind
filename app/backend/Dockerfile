# Dockerfile for MergeMind API service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/backend/fastapi_app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code selectively to avoid cache files
COPY app/backend/fastapi_app/main.py .
COPY app/backend/fastapi_app/routers/ ./routers/
COPY app/backend/fastapi_app/services/ ./services/
COPY app/backend/fastapi_app/middleware/ ./middleware/
COPY app/ai/ ./ai/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/healthz || exit 1

# Run the application
CMD ["python", "main.py"]
