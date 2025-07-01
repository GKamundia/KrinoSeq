# Railway deployment configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create necessary directories
RUN mkdir -p data/uploads data/results

# Expose port
EXPOSE $PORT

# Start the application
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
