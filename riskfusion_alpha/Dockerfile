# Build Stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY pyproject.toml .
COPY riskfusion riskfusion/
COPY README.md .
# Install dependencies (requires source for setuptools to be happy or complex hacks)
RUN pip install --upgrade pip
RUN pip install ".[dev]" --no-cache-dir

# Runtime Stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r riskfusion && useradd -r -g riskfusion riskfusion

# Install runtime deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder (site-packages)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY . .

# Install the app itself (links egg-info)
RUN pip install --no-deps -e .

# Create data directories and chown
RUN mkdir -p data/raw data/processed data/models data/outputs data/audit \
    && chown -R riskfusion:riskfusion /app/data

USER riskfusion

# Default command: show help
CMD ["riskfusion", "--help"]
