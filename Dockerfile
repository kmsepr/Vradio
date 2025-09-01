# Use official lightweight Python image
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run app with Gunicorn on port 8000
CMD ["gunicorn", "-k", "gevent", "-b", "0.0.0.0:8000", "stream:app"]