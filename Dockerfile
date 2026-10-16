FROM python:3.12-slim

# Prevent Python from writing .pyc files & ensure unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install minimal build tools and curl for healthcheck and uv installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency specifications first for optimal layer caching
COPY pyproject.toml requirements.txt ./

# Install Python dependencies using uv into system environment
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application source code and configurations
COPY config/ config/
COPY src/ src/
COPY pipeline/ pipeline/
COPY utils/ utils/
COPY static/ static/
COPY templates/ templates/
COPY artifacts/ artifacts/
COPY application.py ./

# Security: Create unprivileged system user & group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /app -s /sbin/nologin appuser && \
    mkdir -p /app/logs /tmp && \
    chown -R appuser:appgroup /app /tmp && \
    chmod -R 755 /app

# Switch to non-root user
USER 10001:10001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["python", "application.py"]
