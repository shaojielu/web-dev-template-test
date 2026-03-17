FROM ghcr.io/astral-sh/uv:0.10.11 AS uv

FROM python:3.13 AS builder

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN python -m venv .venv

COPY backend/pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

COPY backend/app /app/app
COPY backend/alembic.ini /app/alembic.ini
COPY backend/alembic /app/alembic
COPY backend/scripts /app/scripts

RUN addgroup --system app && adduser --system --ingroup app appuser
RUN chown -R appuser:app /app

USER appuser

EXPOSE 8000

WORKDIR /app

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
