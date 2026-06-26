FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

# pyproject.toml is at repo root
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev

# copy agents source into /app
COPY agents/ .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]