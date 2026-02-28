FROM python:3.12-slim

# System dependencies for FFmpeg, video processing, Pillow, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    fonts-dejavu-core \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media directories
RUN mkdir -p /app/media/{voiceovers,footage,thumbnails,final_videos,temp}

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
