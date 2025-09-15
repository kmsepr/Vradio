# -------------------------------
# Stage 1: Builder
# -------------------------------
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install into /install
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt \
    gunicorn gevent flask

# -------------------------------
# Stage 2: Runtime
# -------------------------------
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PATH="/install/bin:$PATH"

# Install runtime dependencies (FFmpeg + minimal libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgcc-s1 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /install
# Copy app code
COPY . /app

# Expose port
EXPOSE 8000

# Start the app
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "gevent", "stream:app"]