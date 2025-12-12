FROM python:3.13-slim as builder

# Install system dependencies for Tesseract, image processing, and build tools
# Combined RUN step ensures proper cleanup for a smaller layer size
RUN apt-get update \
    && apt-get install -y \
        tesseract-ocr \
        libtesseract-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project file
COPY pyproject.toml .

# Install uv first
RUN pip install --no-cache-dir uv

# Install non-PyTorch dependencies using uv
RUN uv pip install --system --no-cache .

# Install PyTorch and Torchvision separately, forcing CPU-only wheels
# RUN uv pip install --system --no-cache \
#     torch==2.9.1 \
#     torchvision==0.24.1 \
#     --extra-index-url https://download.pytorch.org/whl/cpu

FROM python:3.13-slim

# Re-install only essential runtime system dependencies (Tesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .

# Expose port 
EXPOSE 8000

# Start the FastAPI server
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
