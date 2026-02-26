# Career Architect Pro — Production Dockerfile
# Python 3.11 slim; Streamlit UI layer (FastAPI migration target: Phase 2)

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────────────────────
RUN groupadd -r appuser && useradd -r -g appuser appuser

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Dependencies (layer-cached before code copy) ─────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY --chown=appuser:appuser . .

# ── Drop privileges ───────────────────────────────────────────────────────────
USER appuser

# ── Healthcheck (Streamlit default port 8501) ─────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" \
    || exit 1

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    LOG_FORMAT=json \
    LOG_LEVEL=INFO

EXPOSE 8501

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["python", "-m", "streamlit", "run", "app/ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
