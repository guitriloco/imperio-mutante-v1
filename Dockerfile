# syntax=docker/dockerfile:1.4

# ==========================================
# Stage 1: Build & Dependency Wheel Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ==========================================
# Stage 2: Minimal Production Runtime
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    KNOWLEDGE_DIR=/app/02_CONHECIMENTO \
    DATA_DIR=/app/api_mutante/data

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r -g 1001 mutante \
    && useradd -r -u 1001 -g mutante -s /bin/bash -m mutante

COPY --from=builder /build/wheels /tmp/wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels

COPY --chown=mutante:mutante api_mutante /app/api_mutante
COPY --chown=mutante:mutante interface_dashboard /app/interface_dashboard

RUN mkdir -p /app/02_CONHECIMENTO /app/api_mutante/data /app/api_mutante/prompts \
    && chown -R mutante:mutante /app

USER mutante

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "api_mutante.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--lifespan", "on"]
