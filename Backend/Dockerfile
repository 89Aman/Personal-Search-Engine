# Use a modern Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8080

# Command to run the application
# We use 0.0.0.0 to allow external connections (required for Cloud Run)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
