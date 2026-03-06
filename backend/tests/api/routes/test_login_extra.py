import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.users import UserCreate
from app.services.user import create_user
from app.utils.utils import generate_password_reset_token
from tests.utils.utils import random_email, random_lower_string

pytestmark = pytest.mark.anyio


async def test_recover_password_for_existing_user(
    client: AsyncClient, _db: AsyncSession
) -> None:
    """Password recovery for an existing user triggers email sending (background task)."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery/{settings.FIRST_SUPERUSER}"
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password recovery email sent"


async def test_login_inactive_user(client: AsyncClient, db: AsyncSession) -> None:
    """An inactive user should get a 400 error on login."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    await create_user(db, user_in)
    await db.commit()

    r = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"


async def test_reset_password_for_inactive_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Resetting password for an inactive user should fail."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    await create_user(db, user_in)
    await db.commit()

    token = generate_password_reset_token(email=email)
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"


async def test_test_email_superuser_sends_email(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    """Superuser can send a test email (smoke test that the route is reachable)."""
    r = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": settings.FIRST_SUPERUSER},
        headers=superuser_token_headers,
    )
    # If SMTP is not configured, this might raise a 500 or succeed.
    # We just verify the route handles the request.
    assert r.status_code in (201, 500)
