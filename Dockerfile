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

# Copy all app files
COPY . .

# Create necessary directories (optional for uploads/logos)
RUN mkdir -p static/logos

# Run Flask directly (good for personal, low-load apps)
CMD ["python", "stream.py"]