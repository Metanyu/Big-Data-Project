FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency metadata first (cache-friendly)
COPY pyproject.toml uv.lock ./

# Install deps
RUN uv sync

# Copy producer code
COPY kafka/producer.py ./producer.py

CMD ["uv", "run", "python", "producer.py"]
