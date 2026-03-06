# Testing and Configuration Patterns

Annotated examples for backend testing, environment configuration, and development commands.

## Test Fixtures

Source: `backend/tests/conftest.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, engine
from app.main import app
from app.models.base import Base

pytestmark = pytest.mark.anyio  # Required for all async test modules

@pytest.fixture(scope="session", autouse=True)
async def setup_db() -> None:
    """Create database tables once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession]:
    """Function-scoped DB session. Cleans up non-superuser data after each test."""
    async with async_session() as session:
        await init_db(session)
        yield session
        await session.rollback()
        # Cleanup test data
        await session.execute(delete(User).where(User.email != settings.FIRST_SUPERUSER))
        await session.commit()

@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Test HTTP client. Depends on db fixture for initialization."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

@pytest.fixture(scope="function")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    """Auth headers for superuser."""
    return await get_superuser_token_headers(client)

@pytest.fixture(scope="function")
async def normal_user_token_headers(client: AsyncClient, db: AsyncSession) -> dict[str, str]:
    """Auth headers for normal user."""
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
```

Available fixtures:
| Fixture | Scope | Purpose |
|---|---|---|
| `db` | function | AsyncSession for direct DB operations |
| `client` | function | AsyncClient for HTTP requests |
| `superuser_token_headers` | function | `{"Authorization": "Bearer <token>"}` for admin |
| `normal_user_token_headers` | function | `{"Authorization": "Bearer <token>"}` for regular user |

## Route Test Pattern

Source: `backend/tests/api/routes/test_customers.py`

```python
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.customers import CustomerCreate
from app.services.customer import create_customer

pytestmark = pytest.mark.anyio  # REQUIRED at module level

# Test: unauthenticated access returns 401
async def test_read_products_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/products/")
    assert response.status_code == 401

# Test: authenticated CRUD through API
async def test_read_products_with_pagination(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    # Setup: create test data via service functions
    await create_product(
        db,
        ProductCreate(name=f"Product-{uuid.uuid4()}", price=Decimal("9.99")),
    )
    await db.commit()  # Must commit in tests (no auto-commit in test session)

    # Act: call API endpoint
    response = await client.get(
        f"{settings.API_V1_STR}/products/?skip=0&limit=10",
        headers=superuser_token_headers,
    )

    # Assert: check response
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert len(payload["data"]) >= 1

# Test: validation errors return 422
async def test_read_products_limit_out_of_range(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/products/?skip=0&limit=501",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422
```

Key points:

- Always add `pytestmark = pytest.mark.anyio` at module level
- Use service functions to create test data, then test through the HTTP client
- Call `await db.commit()` after creating test data (test sessions don't auto-commit)
- Test these scenarios: 401 (no auth), 200 (success), 422 (validation), 404 (not found)
- Use `f"{settings.API_V1_STR}/resource/"` for URL construction
- Use `uuid.uuid4()` in test data to avoid collisions between test runs

## Environment Variables

Source: `.env` (root) and `backend/app/core/config.py`

The backend reads all config from the root `.env` file via Pydantic Settings.

Required variables:

```bash
PROJECT_NAME=MyApp
SECRET_KEY=changethis            # MUST change for deployment
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis  # MUST change for deployment
POSTGRES_SERVER=db               # 'db' in Docker, 'localhost' locally
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=aabbccpostgres
POSTGRES_DB=app
ENVIRONMENT=local                # local | test | staging | production
```

Frontend env vars (in `frontend/.env.local` for local dev outside Docker):

```bash
API_BASE_URL=http://localhost:8000       # Server-side API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000  # Client-side (if needed)
```

## Alembic Migration Workflow

After creating or modifying a model:

```bash
cd backend

# 1. Generate migration
uv run alembic revision --autogenerate -m "Add product table"

# 2. Review the generated file in backend/alembic/versions/
#    Verify it creates the correct table, columns, indexes, and constraints

# 3. Apply migration
uv run alembic upgrade head

# 4. If something is wrong, rollback
uv run alembic downgrade -1
```

Common issues:

- **Model not detected**: Ensure it's imported in `models/__init__.py`
- **Empty migration**: The model might already be reflected in the DB schema
- **Relationship errors**: Check that both sides of a relationship reference each other correctly

## Test Commands

```bash
cd backend

# Full test suite
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres \
  uv run pytest

# Single test file
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres \
  uv run pytest tests/api/routes/test_products.py

# Single test by name
ENVIRONMENT=test POSTGRES_DB=app_test POSTGRES_SERVER=localhost \
  POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=aabbccpostgres \
  uv run pytest tests/api/routes/test_products.py -k "test_create_product"

# With coverage report
uv run bash scripts/test.sh
```

## Lint Commands

```bash
cd backend
uv run ruff check app          # Lint check
uv run ruff format app --check # Format check
uv run ruff format app         # Auto-format
uv run mypy app                # Type checking (strict, excludes tests)
uv run bash scripts/lint.sh    # All checks at once
```

## Docker Commands

```bash
# Start all services (with hot reload)
docker compose watch

# Start specific services
docker compose up -d db backend frontend

# Run E2E tests
docker compose up -d
docker compose run --rm playwright npx playwright test
docker compose run --rm playwright npx playwright test tests/products.spec.ts

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```
