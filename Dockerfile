# -------------------------------
# Base image
# -------------------------------
FROM python:3.11-slim

# -------------------------------
# Environment setup
# -------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# -------------------------------
# Install system dependencies including ffmpeg
# -------------------------------
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------
# Set working directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Copy project files
# -------------------------------
COPY . .

# -------------------------------
# Install Python dependencies
# -------------------------------
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# -------------------------------
# Expose the port
# -------------------------------
EXPOSE 8000

# -------------------------------
# Command to run the app
# -------------------------------
CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:8000", "stream:app"]