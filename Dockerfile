# Use a slim official Python image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        tzdata \
        && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Optional: create directories for static content
RUN mkdir -p static/logos

# Expose the port Flask runs on
EXPOSE 8000

# Start the Flask app
CMD ["python", "stream.py"]