FROM python:3.11-slim

# Set environment variables for writable cache directories
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/tmp/nltk_data \
    TRANSFORMERS_CACHE=/tmp/transformers_cache \
    HF_HOME=/tmp/huggingface \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create writable cache directories
RUN mkdir -p /tmp/nltk_data /tmp/transformers_cache /tmp/huggingface

# Install Python dependencies
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy your application code
COPY main.py .
COPY backend/ ./backend/

# Expose the port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
