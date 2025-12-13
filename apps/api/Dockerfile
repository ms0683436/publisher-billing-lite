FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (for build cache)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

EXPOSE 8000

# Default dev command with hot reload
CMD ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
