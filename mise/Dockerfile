# Use Python 3.12 slim as base
FROM python:3.12-slim-bookworm AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package definition
COPY pyproject.toml README.md ./
COPY src/ src/

# Install package
RUN pip install --no-cache-dir .

# Production stage
FROM python:3.12-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system app && useradd --system --gid app app

# Set working directory
WORKDIR /app

# Copy installed package from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/mcp-server-mise /usr/local/bin/

# Install mise
RUN curl https://mise.run | sh && \
    ln -s ~/.local/bin/mise /usr/local/bin/mise

# Switch to non-root user
USER app

# Set entrypoint
ENTRYPOINT ["mcp-server-mise"]
