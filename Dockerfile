# Use a minimal base image with Python and FFmpeg
FROM python:3.11-slim

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your app code
COPY stream.py .

# Install dependencies
RUN pip install flask gunicorn

# Expose the port Flask/Gunicorn runs on
EXPOSE 8000

# Start Gunicorn with 4 workers and bind to port 8000
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "stream:app"]