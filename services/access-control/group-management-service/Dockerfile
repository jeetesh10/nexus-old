FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py .
COPY admin_interface.html .

# Create database directory
RUN mkdir -p /app/database

# Copy database schema and initialize database
COPY database/schema.sql /app/database/
RUN sqlite3 /app/database/services.db < /app/database/schema.sql

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8083/health', timeout=5)"

# Run the application
CMD ["python", "api_server.py"]
