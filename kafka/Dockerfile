# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv via pip to decouple from base image updates if needed
RUN pip install --no-cache-dir uv

# Copy dependency definition
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
# --frozen ensures we stick to the lockfile
RUN uv sync --frozen

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY kafka/producer.py ./producer.py

# Add virtualenv to PATH so we can run python/uv commands directly
ENV PATH="/app/.venv/bin:$PATH"

# Run the producer directly with python (no need for uv run overhead in runtime)
CMD ["python", "producer.py"]
