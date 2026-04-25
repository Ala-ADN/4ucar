# Base image for all FastAPI services. No version pinning — pin in CI/prod overrides.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        tesseract-ocr \
        tesseract-ocr-fra \
        tesseract-ocr-ara \
        poppler-utils \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv pip install --system .

COPY backend ./backend

EXPOSE 8000
CMD ["uvicorn", "backend.services.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
