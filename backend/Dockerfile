# Project AEGIS Backend Dockerfile
# Multi-stage build for optimal size and security

# Build stage
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Production stage
FROM python:3.10-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    AEGIS_ENV=production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libgdal33 \
    libproj22 \
    libgeos-c1v5 \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r aegis && useradd -r -g aegis aegis

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directories
RUN mkdir -p /app /app/logs /app/uploads /app/static /app/temp && \
    chown -R aegis:aegis /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=aegis:aegis . .

# Copy configuration templates
COPY --chown=aegis:aegis docker/config/docker.env.template /app/.env.template
COPY --chown=aegis:aegis docker/config/docker-uwsgi.ini /app/uwsgi.ini

# Create startup scripts
COPY --chown=aegis:aegis docker/scripts/entrypoint.sh /app/entrypoint.sh
COPY --chown=aegis:aegis docker/scripts/wait-for-it.sh /app/wait-for-it.sh

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/wait-for-it.sh

# Switch to non-root user
USER aegis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set volumes for persistent data
VOLUME ["/app/logs", "/app/uploads", "/app/temp"]

# Default command
CMD ["/app/entrypoint.sh"]