from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_refresh_token
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
    assert "refresh_token" in tokens
    assert tokens["refresh_token"]


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


async def test_refresh_token_success(client: AsyncClient) -> None:
    """Test that a valid refresh token returns a new token pair."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    refresh_token = tokens["refresh_token"]

    r = await client.post(
        f"{settings.API_V1_STR}/login/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r.status_code == 200
    new_tokens = r.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"]
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"]

    # Verify the new access token works
    r = await client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert r.status_code == 200


async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Test that an invalid refresh token is rejected."""
    r = await client.post(
        f"{settings.API_V1_STR}/login/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert r.status_code == 401


async def test_refresh_token_with_access_token_rejected(client: AsyncClient) -> None:
    """Test that using an access token as refresh token is rejected."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    access_token = tokens["access_token"]

    r = await client.post(
        f"{settings.API_V1_STR}/login/refresh",
        json={"refresh_token": access_token},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid token type"


async def test_refresh_token_expired(client: AsyncClient) -> None:
    """Test that an expired refresh token is rejected."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200

    # Decode the refresh token to get the user id, then create an expired one
    tokens = r.json()
    # Create a refresh token that's already expired
    import jwt

    payload = jwt.decode(
        tokens["refresh_token"], settings.SECRET_KEY, algorithms=["HS256"]
    )
    expired_token = create_refresh_token(
        subject=payload["sub"],
        expires_delta=timedelta(seconds=-1),
    )

    r = await client.post(
        f"{settings.API_V1_STR}/login/refresh",
        json={"refresh_token": expired_token},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Refresh token expired"
