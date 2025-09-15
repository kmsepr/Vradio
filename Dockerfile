# -------------------------------
# Base image
# -------------------------------
FROM python:3.11-slim

# -------------------------------
# Environment
# -------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# -------------------------------
# Install system dependencies
# -------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        git \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Set workdir
# -------------------------------
WORKDIR /app

# -------------------------------
# Copy app
# -------------------------------
COPY . /app

# -------------------------------
# Install Python dependencies
# -------------------------------
RUN pip install --no-cache-dir -r requirements.txt \
    gunicorn gevent flask

# -------------------------------
# Expose port
# -------------------------------
EXPOSE 8000

# -------------------------------
# Start app
# -------------------------------
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "gevent", "stream:app"]