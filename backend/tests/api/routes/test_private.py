import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.schemas.users import PrivateUserCreate
from app.services.user import get_user_by_email
from tests.utils.utils import random_email, random_lower_string

pytestmark = pytest.mark.anyio


async def test_create_user(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = PrivateUserCreate(
        email=username, password=password, full_name="Test User"
    )
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
        headers=superuser_token_headers,
    )
    assert 200 <= response.status_code < 300
    created_user = response.json()
    user = await get_user_by_email(db, username)
    assert user
    assert user.email == created_user["email"]
    assert user.full_name == "Test User"


async def test_create_user_verify_password(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = PrivateUserCreate(
        email=username,
        password=password,
        full_name="Test User Password",
    )
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
        headers=superuser_token_headers,
    )
    assert response.status_code == 201

    user = await get_user_by_email(db, username)
    assert user
    assert verify_password(password, user.hashed_password)


async def test_create_user_default_values(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    user_in = PrivateUserCreate(
        email=random_email(),
        password=random_lower_string(),
        full_name="Default Values Test",
    )
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    created_user = response.json()

    assert created_user["is_active"] is True
    assert created_user["is_superuser"] is False


async def test_create_user_response_fields(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    user_in = PrivateUserCreate(
        email=random_email(),
        password=random_lower_string(),
        full_name="Response Fields Test",
    )
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    created_user = response.json()

    assert "id" in created_user
    assert "email" in created_user
    assert "full_name" in created_user
    assert "is_active" in created_user
    assert "is_superuser" in created_user
    assert "password" not in created_user
    assert "hashed_password" not in created_user


async def test_create_user_can_login(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = PrivateUserCreate(
        email=username,
        password=password,
        full_name="Login Test User",
    )

    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
        headers=superuser_token_headers,
    )
    assert response.status_code == 201

    login_data = {"username": username, "password": password}
    login_response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert tokens["access_token"]


async def test_create_multiple_users(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    users_data: list[PrivateUserCreate] = []
    for i in range(3):
        users_data.append(
            PrivateUserCreate(
                email=random_email(),
                password=random_lower_string(),
                full_name=f"Test User {i}",
            )
        )

    for user_in in users_data:
        response = await client.post(
            f"{settings.API_V1_STR}/private/users/",
            json=user_in.model_dump(),
            headers=superuser_token_headers,
        )
        assert response.status_code == 201

    for user_in in users_data:
        user = await get_user_by_email(db, user_in.email)
        assert user is not None
        assert user.email == user_in.email
