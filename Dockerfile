FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY agents/pyproject.toml agents/uv.lock* ./

RUN uv sync --frozen --no-dev

COPY agents/ .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]