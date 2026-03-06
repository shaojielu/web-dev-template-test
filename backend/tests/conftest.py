from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, engine
from app.initial_data import init_db
from app.main import app
from app.models.base import Base
from app.models.user import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Provide an asyncio backend for the entire test session."""
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_db() -> None:
    """Create database tables (session-scoped, runs once)."""
    if settings.ENVIRONMENT in {"staging", "production"}:
        raise RuntimeError(
            "Refusing to run destructive test setup in staging/production. "
            "Use local/test environment for running tests."
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession]:
    """
    Get a database session (function-scoped).
    Each test function gets an independent session; non-superuser data is cleaned up afterward.
    """
    async with async_session() as session:
        # Ensure superuser exists
        await init_db(session)
        yield session
        # Rollback uncommitted changes
        await session.rollback()
        # Only clean up non-superuser test data; keep superuser for efficiency
        await session.execute(
            delete(User).where(User.email != settings.FIRST_SUPERUSER)
        )
        await session.commit()


@pytest.fixture(scope="function")
async def client(_db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Get a test client (function-scoped); depends on db to ensure database is initialized."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(scope="function")
async def superuser_token_headers(
    client: AsyncClient, _db: AsyncSession
) -> dict[str, str]:
    """Get superuser authentication headers (function-scoped)."""
    return await get_superuser_token_headers(client)


@pytest.fixture(scope="function")
async def normal_user_token_headers(
    client: AsyncClient, db: AsyncSession
) -> dict[str, str]:
    """Get normal user authentication headers (function-scoped)."""
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
