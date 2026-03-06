import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio


async def test_health_check(client: AsyncClient) -> None:
    """Test the health check endpoint."""
    response = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    """Test that the health check endpoint does not require authentication."""
    # No authentication headers
    response = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200


async def test_test_email_requires_superuser(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that the test email endpoint requires superuser privileges."""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges"


async def test_test_email_no_auth(client: AsyncClient) -> None:
    """Test that the test email endpoint requires authentication."""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
    )
    assert response.status_code == 401


async def test_test_email_invalid_email(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test that the test email endpoint validates email format."""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "invalid-email"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 422  # Validation error


async def test_test_email_success(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the test email endpoint succeeds when email sending works."""
    monkeypatch.setattr("app.api.routes.utils.send_email", lambda **kwargs: None)
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Test email sent"
