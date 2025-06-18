# Use an official lightweight Python image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Create necessary directories
RUN mkdir -p static/logos

# Explicitly set the command (critical for Koyeb)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "stream:app"]