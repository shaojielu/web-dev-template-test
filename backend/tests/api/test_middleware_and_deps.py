import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM

pytestmark = pytest.mark.anyio


async def test_request_id_header_returned(client: AsyncClient) -> None:
    """Test that X-Request-ID header is returned on every response."""
    r = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert "X-Request-ID" in r.headers


async def test_custom_request_id_echoed(client: AsyncClient) -> None:
    """Test that a custom X-Request-ID is echoed back."""
    custom_id = "test-request-id-12345"
    r = await client.get(
        f"{settings.API_V1_STR}/utils/health-check/",
        headers={"X-Request-ID": custom_id},
    )
    assert r.headers["X-Request-ID"] == custom_id


async def test_security_headers_present(client: AsyncClient) -> None:
    """Test that security headers are set on all responses."""
    r = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in r.headers


async def test_security_headers_include_hsts_in_production(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HSTS header should be emitted in production mode."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    r = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert (
        r.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"
    )


async def test_invalid_token_returns_403(client: AsyncClient) -> None:
    """Test that a completely invalid JWT token returns 403."""
    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer garbage.invalid.token"},
    )
    assert r.status_code == 403


async def test_access_token_with_no_sub_returns_403(client: AsyncClient) -> None:
    """Token without 'sub' claim should be rejected."""
    token = jwt.encode(
        {"type": "access"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


async def test_non_access_token_type_returns_403(client: AsyncClient) -> None:
    """Token with wrong type claim should be rejected."""
    token = jwt.encode(
        {"sub": "some-user-id", "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


async def test_token_for_deleted_user_returns_401(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A valid token for a user that has been deleted should return 401."""
    from datetime import timedelta

    from app.core.security import create_access_token
    from app.schemas.users import UserCreate
    from app.services.user import create_user, delete_user

    user_in = UserCreate(
        email="deleteme@example.com", password="testpassword123", is_active=True
    )
    user = await create_user(db, user_in)
    await db.commit()

    token = create_access_token(subject=user.id, expires_delta=timedelta(minutes=30))

    await delete_user(db, user)
    await db.commit()

    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "User not found"


async def test_inactive_user_rejected_by_active_user_dep(
    client: AsyncClient, db: AsyncSession
) -> None:
    """An inactive user should be rejected with 400 when accessing protected endpoints."""
    from datetime import timedelta

    from app.core.security import create_access_token
    from app.schemas.users import UserCreate
    from app.services.user import create_user

    user_in = UserCreate(
        email="inactive@example.com",
        password="testpassword123",
        is_active=False,
    )
    user = await create_user(db, user_in)
    await db.commit()

    token = create_access_token(subject=user.id, expires_delta=timedelta(minutes=30))

    r = await client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"
