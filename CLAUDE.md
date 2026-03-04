# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack web application: **FastAPI** (Python 3.13) backend + **Next.js** (React 19) frontend, with PostgreSQL, Docker Compose, and Traefik reverse proxy.

## Common Commands

### Development Environment

```bash
# Start all services (db, backend, frontend, mailcatcher, traefik, adminer)
docker compose watch

# Windows alternative (handles port 5432 conflicts)
.\scripts\dev-up.ps1    # start
.\scripts\dev-down.ps1  # stop

# Run frontend locally (after stopping docker frontend)
docker compose stop frontend
cd frontend && pnpm dev

# Run backend locally (after stopping docker backend)
docker compose stop backend
cd backend && fastapi run --reload app/main.py
```

### Backend Tests (Pytest)

Tests require `ENVIRONMENT=test` and `POSTGRES_DB` ending with `_test` — the test suite aborts otherwise.

```bash
# Ensure db is running
docker compose up -d db

# Run all tests (from backend/)
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres uv run pytest

# Run a single test file
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres uv run pytest tests/api/test_users.py

# Run a single test by name
... uv run pytest tests/api/test_users.py -k "test_create_user"

# Run with coverage
cd backend && uv run bash scripts/test.sh
```

### Backend Linting & Formatting

```bash
cd backend
uv run ruff check app          # lint
uv run ruff format app --check # format check
uv run ruff format app         # auto-format
uv run mypy app                # type checking (strict mode, excludes tests)

# All lint checks at once
uv run bash scripts/lint.sh
```

### Frontend

```bash
cd frontend
pnpm install       # install dependencies
pnpm dev           # dev server on :3000
pnpm build         # production build
pnpm lint          # ESLint
```

### Frontend E2E Tests (Playwright)

```bash
# Via Docker (recommended, runs against full stack)
docker compose up -d
docker compose run --rm playwright npx playwright test

# Run specific test file
docker compose run --rm playwright npx playwright test tests/auth.spec.ts
```

### Database Migrations (Alembic)

```bash
cd backend

# Generate migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

### Pre-commit Hooks

Uses `prek` (configured in `.pre-commit-config.yaml`): ruff check/format, mypy, eslint, no-commit-to-branch (main).

```bash
cd backend
uv run prek install -f    # install hooks
uv run prek run --all-files  # run manually
```

## Architecture

### Backend (FastAPI)

Layered architecture under `backend/app/`:

```
api/routes/   → HTTP route handlers (thin controllers)
api/deps.py   → FastAPI dependencies (SessionDep, CurrentUserDep, CurrentActiveUserDep)
services/     → Business logic (called by routes, receives session)
models/       → SQLAlchemy ORM models (User, Customer, Invoice) inheriting from models/base.py Base
schemas/      → Pydantic request/response models
core/config.py → Pydantic Settings (reads ../.env)
core/db.py    → Async SQLAlchemy engine + session factory
core/security.py → JWT creation + password hashing (bcrypt)
```

**Request flow**: Route handler → injects `SessionDep` + `CurrentUserDep` via FastAPI Depends → calls service function → service queries/mutates via SQLAlchemy session → route returns Pydantic schema.

**DB session lifecycle** (`api/deps.py`): session auto-commits on success, rolls back on exception. Each request gets its own session.

**API prefix**: All routes under `/api/v1`. A `private` router is included only in `local`/`test` environments.

**Models** use async SQLAlchemy 2.0 with `asyncpg` driver. Alembic migrations are async-aware (`backend/alembic/env.py`).

### Frontend (Next.js)

Uses **App Router** with server components and server actions:

```
app/
  dashboard/        → Protected routes (overview, customers, invoices)
  login/, logout/   → Auth pages
  lib/
    api.ts          → Server-side apiFetch() wrapper (reads token from cookies, auto-redirects on 401)
    actions.ts      → Server Actions (form mutations)
    data.ts         → Data fetching functions
    definitions.ts  → TypeScript type definitions
  ui/               → Reusable UI components
```

**Auth**: JWT stored in HTTP cookie (`access_token`). `apiFetch()` auto-attaches Bearer token from cookies. Client-side `isTokenExpired()` in `lib/auth.ts`.

**API communication**: Server components use `apiFetch()` (server-only, imports `next/headers`). Client mutations use Server Actions in `lib/actions.ts`.

**Env vars**: `API_BASE_URL` for server-side requests (defaults to `http://localhost:8000`), `NEXT_PUBLIC_API_BASE_URL` for any client-side needs.

### Docker Compose

- `compose.yml`: Production config (db, prestart, backend, frontend)
- `compose.override.yml`: Dev overrides (adds traefik, mailcatcher, adminer, playwright, volume mounts, port mappings)
- Services: `db` (:5432), `backend` (:8000), `frontend` (:3000), `adminer` (:8080), `traefik` (:8090), `mailcatcher` (:1080)

### Configuration

All config flows through the root `.env` file. Backend reads it via Pydantic Settings (`env_file="../.env"`). Frontend uses `frontend/.env.local` for local dev outside Docker.

Critical settings: `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD` must be changed from defaults before deployment.

## Key Patterns

- **Backend dependency injection**: Use `SessionDep`, `CurrentUserDep`, `CurrentActiveUserDep` type aliases from `api/deps.py` in route function signatures
- **Async throughout**: All backend DB operations, route handlers, and tests use async/await
- **Test fixtures**: `conftest.py` provides `db`, `client`, `superuser_token_headers`, `normal_user_token_headers` fixtures; tests use `pytest.mark.anyio`
- **Adding new models**: Create model in `models/`, import it in `models/__init__.py` (needed for Alembic autogenerate), create schema in `schemas/`, service in `services/`, route in `api/routes/`, register route in `api/main.py`
