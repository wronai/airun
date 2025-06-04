# AIRun Docker Image
# Multi-stage build for optimal image size

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main --no-interaction --no-ansi

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    nodejs \
    npm \
    php-cli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r airun && useradd -r -g airun airun

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /opt/venv/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /opt/venv/bin

# Copy application code
COPY airun/ /app/airun/
COPY pyproject.toml /app/

# Set working directory
WORKDIR /app

# Install the application
RUN pip install -e .

# Create airun directories
RUN mkdir -p /home/airun/.airun/{logs,cache,backups} && \
    chown -R airun:airun /home/airun

# Switch to non-root user
USER airun

# Set home directory
ENV HOME=/home/airun

# Create default configuration
RUN airun config --init

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD airun doctor || exit 1

# Default command
CMD ["airun", "--help"]

# Development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for development
RUN pip install poetry

# Copy development files
COPY tests/ /app/tests/
COPY Makefile /app/
COPY .pre-commit-config.yaml /app/

# Install development dependencies
RUN poetry install --with dev,test --no-interaction --no-ansi

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Switch back to airun user
USER airun

# Set development environment
ENV AIRUN_DEBUG=true

# Default command for development
CMD ["bash"]