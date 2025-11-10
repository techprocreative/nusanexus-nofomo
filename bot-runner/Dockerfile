# NusaNexus NoFOMO - Bot Runner Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Freqtrade
RUN pip install freqtrade==1.14.0

# Copy application code
COPY . .

# Create directories for bot data
RUN mkdir -p /app/data/{configs,strategies,logs}

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (if needed for monitoring)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the bot runner (in production this would be managed by Redis queue)
CMD ["python", "bot_runner.py"]