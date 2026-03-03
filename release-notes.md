# Release Notes

## Latest Changes

### 0.1.0

- Initial project setup with FastAPI + Next.js full stack template
- User authentication with JWT (access tokens with type claims)
- Rate limiting on login and password recovery endpoints
- Security headers on both frontend and backend
- Next.js middleware for unified auth checking
- Background email sending via FastAPI BackgroundTasks
- Health check with database connectivity verification
- Request ID tracking via X-Request-ID header
- Graceful shutdown with database connection pool disposal
- Docker Compose + Traefik + Docker Swarm deployment support
- Playwright E2E testing with 4-shard parallelism
- Example invoice/customer management dashboard
