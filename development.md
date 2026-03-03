# FastAPI + Next.js Project - Development

## Docker Compose

* Start the local environment using Docker Compose:

```bash
docker compose watch
```

* Or build and run directly without watch:

```bash
docker compose up -d --build
```

### Windows One-Click Script (Recommended)

If you are developing on Windows and another container is already occupying port `5432` on your machine, use the following script instead:

```powershell
.\scripts\dev-up.ps1
```

The script will automatically:

* Detect and temporarily stop any container occupying port `5432`;
* Start `db/backend/frontend/mailcatcher`;
* Verify backend and frontend health checks.

When you are done developing, run:

```powershell
.\scripts\dev-down.ps1
```

This script will shut down the current project containers and restore any previously stopped containers that were occupying port `5432`.

* Once started, the following addresses are available:

Frontend (Next.js): <http://localhost:3000>

Backend (OpenAPI JSON API): <http://localhost:8000>

Swagger UI (Backend Interactive Docs): <http://localhost:8000/docs>

Adminer (Database Management): <http://localhost:8080>

Traefik UI (View Routes): <http://localhost:8090>

MailCatcher (Local SMTP UI): <http://localhost:1080>

**Note**: The first startup may take some time as the backend waits for the database to be ready and completes initialization. You can monitor the startup process through the logs.

View logs (open another terminal):

```bash
docker compose logs
```

View logs for a specific service, for example:

```bash
docker compose logs backend
```

## MailCatcher

MailCatcher is a simple local SMTP service that captures emails sent by the backend in the development environment and displays them in a web interface.

Use cases:

* Testing email functionality
* Verifying email content and formatting
* Debugging email-related issues without sending real emails

The local Docker Compose automatically configures the backend to use MailCatcher (SMTP port 1025). Visit <http://localhost:1080> to view captured emails.

## Local Development

Docker Compose exposes each service on different ports on `localhost`.

The backend and frontend use the same ports as the local development servers: backend at `http://localhost:8000`, frontend at `http://localhost:3000`.

This allows you to stop a Docker service and switch to a local development server while keeping the ports consistent.

The local `docker compose` maps PostgreSQL to `localhost:5432` by default.

For example, stop the `frontend` service and start the local frontend:

```bash
docker compose stop frontend
cd frontend
pnpm dev
```

When developing Next.js locally, you need to configure the API address (e.g., in `frontend/.env.local`):

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
```

Or stop the `backend` service and start the local backend:

```bash
docker compose stop backend
cd backend
fastapi run --reload app/main.py
```

## Running Backend Tests (Pytest)

Backend tests include destructive database operation protection and require:

* `ENVIRONMENT=test`
* `POSTGRES_DB` ending with `_test` (e.g., `app_test`)

Recommended command (in the `backend/` directory):

```bash
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=changethis uv run pytest
```

If you first start the database from the project root directory:

```bash
docker compose up -d db
```

You can use the following single command to set up a minimal test environment and run the tests:

```bash
cp .env.example .env && \
sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT=test/' .env && \
sed -i 's/^POSTGRES_DB=.*/POSTGRES_DB=app_test/' .env && \
cd backend && uv run pytest
```

## Docker Compose with `localhost.tiangolo.com`

By default, Docker Compose uses `localhost` and assigns different ports to each service.

In production (or staging) environments, services typically run on different subdomains, such as `api.example.com` and `dashboard.example.com`.

The [deployment](deployment.md) guide contains Traefik-related instructions, which handles routing traffic to the corresponding services based on subdomains.

If you want to simulate this subdomain-based access locally, modify the `.env` file in the root directory:

```dotenv
DOMAIN=localhost.tiangolo.com
```

Docker Compose will use this domain to configure the services.

Traefik will route `api.localhost.tiangolo.com` to the backend and `dashboard.localhost.tiangolo.com` to the frontend.

`localhost.tiangolo.com` is a special domain where all subdomains point to `127.0.0.1`, making it convenient for local testing.

After making changes, restart:

```bash
docker compose watch
```

In production environments, Traefik is typically deployed separately outside of Docker Compose. For local development, `compose.override.yml` includes a Traefik instance to facilitate testing subdomain routing.

## Docker Compose Files and Environment Variables

The main configuration file is `compose.yml`, which `docker compose` loads by default.

`compose.override.yml` contains development environment overrides (e.g., mounting source code) and is automatically layered on top of `compose.yml`.

These Docker Compose files use the `.env` file in the root directory to inject environment variables into containers.

They also use additional environment variables set in scripts.

After modifying variables, please restart:

```bash
docker compose watch
```

## .env File

The root `.env` file contains Docker and backend configuration, secrets, passwords, and other sensitive information.

If the project is public, you should avoid committing `.env`. It is recommended to commit `.env.example` and configure real environment variables in CI/CD.

For local Next.js development, use `frontend/.env.local` (or shell environment variables) instead of the root `.env`.

## Pre-commit and Code Standards

The project uses [prek](https://prek.j178.dev/) for code linting and formatting (a modern alternative to Pre-commit).

Once installed, it runs automatically before each git commit to ensure consistent code style.

The configuration file is `.pre-commit-config.yaml` in the root directory.

### Installing prek

`prek` is already included in the project dependencies.

To install the hook locally (enter the `backend` directory):

```bash
cd backend
uv run prek install -f
```

The `-f` flag is used to force installation (in case an old pre-commit hook already exists).

After that, it will run automatically on every `git commit`.

### Running prek Manually

You can also run all checks manually:

```bash
cd backend
uv run prek run --all-files
```

## URLs

Production or staging environments will use the same paths, just with your domain substituted.

### Development URLs

Frontend: <http://localhost:3000>

Backend: <http://localhost:8000>

Swagger UI: <http://localhost:8000/docs>

ReDoc: <http://localhost:8000/redoc>

Adminer: <http://localhost:8080>

Traefik UI: <http://localhost:8090>

MailCatcher: <http://localhost:1080>

### Development URLs with `localhost.tiangolo.com` Configured

Frontend: <http://dashboard.localhost.tiangolo.com>

Backend: <http://api.localhost.tiangolo.com>

Swagger UI: <http://api.localhost.tiangolo.com/docs>

ReDoc: <http://api.localhost.tiangolo.com/redoc>

Adminer: <http://localhost.tiangolo.com:8080>

Traefik UI: <http://localhost.tiangolo.com:8090>

MailCatcher: <http://localhost.tiangolo.com:1080>
