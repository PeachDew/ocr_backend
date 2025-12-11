# Use Python 3.10 slim image for smaller size
FROM python:3.10-slim

# Install system dependencies for Tesseract and image processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Start the FastAPI server
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
