FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project --frozen

# Copy application code
COPY alembic.ini ./
COPY scripts/ ./scripts/
COPY src/ ./src/
COPY tests/ ./tests/

RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]
