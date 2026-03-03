# Frontend (Next.js)

This frontend uses Next.js App Router and integrates with the FastAPI backend.

## Requirements

- Node.js 20+
- pnpm (recommended) or npm

## Environment

The frontend reads the backend URL from:

- `NEXT_PUBLIC_API_BASE_URL` (optional, defaults to `http://localhost:8000`)

## Development

1. Start the backend (`fastapi dev app/main.py`) or `docker compose watch`.
2. Install dependencies:

```bash
pnpm install
```

1. Run the dev server:

```bash
pnpm dev
```

Open `http://localhost:3000` in your browser.

## Login

Use the superuser credentials from the root `.env` file:

- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`

## Production

Build and start:

```bash
pnpm build
pnpm start
```
