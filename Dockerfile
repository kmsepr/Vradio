FROM python:3.11-slim

# Install system dependencies (ffmpeg + required libs)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . /app
WORKDIR /app

# Run with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]