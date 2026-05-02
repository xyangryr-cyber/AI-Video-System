# [SPEC-B-001] Backend image shared by `api` and `worker` services.
# Build context is the repo root (so pyproject.toml and src/ are both visible).

FROM python:3.11-slim

WORKDIR /app

# System deps for common Python libs (psutil, ffmpeg probe, etc.). Keep minimal.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps before copying source so the layer caches well.
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY src ./src

EXPOSE 8000

# Default CMD is for the `api` service; `worker` overrides via compose.
CMD ["uvicorn", "src.backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
