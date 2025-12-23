FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY sync_orders.py .

# Make script executable
RUN chmod +x sync_orders.py

# Set entrypoint
ENTRYPOINT ["python", "sync_orders.py"]

# Default command (can be overridden)
CMD []
