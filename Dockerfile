# syntax=docker/dockerfile:1

# Builder stage: install dependencies into a virtualenv
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /tmp_build
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Runtime stage: slim image with only runtime deps and app code
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app
# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Copy project files
COPY . .
# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
ENV DJANGO_SETTINGS_MODULE=depoauto.settings
# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import socket,os; s=socket.socket(); s.settimeout(3); s.connect(('127.0.0.1', int(os.environ.get('PORT','8000')))); print('ok')" || exit 1
CMD ["/app/entrypoint.sh"]
