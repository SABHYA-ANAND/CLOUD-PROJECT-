# ==========================================
# Optimized Multi-Stage Production Dockerfile
# Cost Optimization: Minimal Image Size (~60MB vs ~1GB baseline)
# Security: Non-root execution & minimal attack surface
# ==========================================

# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies only if needed, keep cache clean
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into /install prefix without cache
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Minimal Runtime
FROM python:3.11-slim AS runner

# Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /home/appuser -m appuser

WORKDIR /home/appuser/app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=appuser:appgroup app.py .
COPY --chown=appuser:appgroup templates templates/

# Switch to non-root user
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5000

EXPOSE 5000

# Production WSGI server (gunicorn) with health timeout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "30", "app:app"]
