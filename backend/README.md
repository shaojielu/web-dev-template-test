# Backend (FastAPI)

Backend service for the template project.

## Stack

- FastAPI
- SQLAlchemy (async) + PostgreSQL
- Alembic migrations
- Pydantic v2 settings/schemas
- Pytest

## Requirements

- Python 3.13+
- `uv` (recommended)
- PostgreSQL (or use Docker Compose from project root)

## Quick Start (recommended with Docker Compose)

From project root:

```bash
cp .env.example .env
docker compose up -d db
```

From `backend/`:

```bash
uv sync
uv run alembic upgrade head
uv run python app/initial_data.py
uv run fastapi run --reload app/main.py
```

API docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Tests

From `backend/`:

```bash
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=changethis uv run pytest
```

Safety guard: tests will abort unless `ENVIRONMENT=test` and `POSTGRES_DB` ends with `_test`.

Coverage:

```bash
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=changethis uv run bash scripts/test.sh
```

## Lint / Format

From `backend/`:

```bash
uv run mypy app
uv run ruff check app
uv run ruff format app
```

Or use helper scripts:

```bash
bash scripts/lint.sh
bash scripts/format.sh
```

## Migrations

Create migration:

```bash
uv run alembic revision --autogenerate -m "your message"
```

Apply migration:

```bash
uv run alembic upgrade head
```
