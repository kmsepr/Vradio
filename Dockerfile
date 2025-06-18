# Use an official lightweight Python image
FROM python:3.9-slim

# Install system dependencies (FFmpeg + SSL for HTTPS streams)
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# First copy requirements to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p static/logos

# Set environment variables
ENV FLASK_APP=stream.py
ENV FLASK_ENV=production

# Expose port 8000
EXPOSE 8000

# Health check (checks if Flask is responsive)
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "stream:app"]