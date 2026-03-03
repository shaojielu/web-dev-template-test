import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.utils.utils import generate_password_reset_token

pytestmark = pytest.mark.anyio


async def test_get_access_token(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


async def test_get_access_token_incorrect_password(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 401


async def test_get_access_token_nonexistent_user(client: AsyncClient) -> None:
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect username or password"


async def test_test_token(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test the test-token endpoint."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert "email" in result
    assert result["email"] == settings.FIRST_SUPERUSER


async def test_test_token_no_auth(client: AsyncClient) -> None:
    """Test that test-token endpoint returns error without authorization."""
    r = await client.post(f"{settings.API_V1_STR}/login/test-token")
    assert r.status_code == 401


async def test_recover_password(client: AsyncClient) -> None:
    """Test password recovery endpoint (returns success even for nonexistent user to prevent enumeration)."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery/nonexistent@example.com"
    )
    # Always returns 200 regardless of user existence to prevent user enumeration
    assert r.status_code == 200
    assert r.json()["message"] == "Password recovery email sent"


async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    """Test resetting password with an invalid token."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": "invalid_token", "new_password": "newpassword123"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"


async def test_reset_password_nonexistent_user(client: AsyncClient) -> None:
    """Test resetting password for a nonexistent user."""
    # Generate a valid-format token for a nonexistent email
    token = generate_password_reset_token(email="nonexistent@example.com")
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r.status_code == 404
    assert "does not exist" in r.json()["detail"]


async def test_reset_password_success(client: AsyncClient) -> None:
    """Test successful password reset."""
    # Generate a token for the superuser
    token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    # Restore original password so other tests are not affected
    token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": settings.FIRST_SUPERUSER_PASSWORD},
    )


async def test_recover_password_html_content(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting password recovery HTML content endpoint."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    # Verify the response contains HTML content
    assert "<!doctype html>" in r.text.lower() or "<html" in r.text.lower()


async def test_recover_password_html_content_nonexistent_user(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting password recovery HTML content for a nonexistent user."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/nonexistent@example.com",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


async def test_recover_password_html_content_no_superuser(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that non-superuser cannot access password recovery HTML content endpoint."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
