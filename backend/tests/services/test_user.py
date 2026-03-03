import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.schemas.users import UserCreate, UserRegister, UserUpdate, UserUpdateMe
from app.services.user import (
    authenticate,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_users,
    set_user_password,
    update_user,
)
from tests.utils.utils import random_email, random_lower_string

pytestmark = pytest.mark.anyio


async def test_create_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)

    user = await create_user(db, user_in)
    await db.commit()

    assert user.email == email
    assert user.full_name == ""
    assert user.is_active is True
    assert user.is_superuser is False
    assert verify_password(password, user.hashed_password)


async def test_create_user_with_full_name(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    user_in = UserRegister(email=email, password=password, full_name=full_name)

    user = await create_user(db, user_in)
    await db.commit()

    assert user.email == email
    assert user.full_name == full_name


async def test_create_superuser(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)

    user = await create_user(db, user_in)
    await db.commit()

    assert user.is_superuser is True


async def test_get_by_id(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    retrieved = await get_user_by_id(db, user.id)

    assert retrieved is not None
    assert retrieved.id == user.id
    assert retrieved.email == email


async def test_get_by_id_not_found(db: AsyncSession) -> None:
    retrieved = await get_user_by_id(db, uuid.uuid4())

    assert retrieved is None


async def test_get_by_email(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    retrieved = await get_user_by_email(db, email)

    assert retrieved is not None
    assert retrieved.id == user.id
    assert retrieved.email == email


async def test_get_by_email_not_found(db: AsyncSession) -> None:
    retrieved = await get_user_by_email(db, "nonexistent@example.com")

    assert retrieved is None


async def test_get_list(db: AsyncSession) -> None:
    await create_user(
        db, UserCreate(email=random_email(), password=random_lower_string())
    )
    await create_user(
        db, UserCreate(email=random_email(), password=random_lower_string())
    )
    await db.commit()

    users, count = await get_users(db)

    assert count >= 2
    assert len(users) >= 2


async def test_get_list_with_pagination(db: AsyncSession) -> None:
    for _ in range(5):
        await create_user(
            db, UserCreate(email=random_email(), password=random_lower_string())
        )
    await db.commit()

    users, count = await get_users(db, skip=0, limit=2)

    assert count >= 5
    assert len(users) == 2


async def test_update_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    new_full_name = random_lower_string()
    user_update = UserUpdateMe(full_name=new_full_name)
    updated = await update_user(db, user, user_update)
    await db.commit()

    assert updated.full_name == new_full_name
    assert updated.email == email


async def test_update_user_email(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    new_email = random_email()
    user_update = UserUpdateMe(email=new_email)
    updated = await update_user(db, user, user_update)
    await db.commit()

    assert updated.email == new_email


async def test_update_user_password(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    new_password = random_lower_string()
    user_update = UserUpdate(password=new_password)
    updated = await update_user(db, user, user_update)
    await db.commit()

    assert verify_password(new_password, updated.hashed_password)


async def test_set_password(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    new_password = random_lower_string()
    await set_user_password(db, user, new_password)
    await db.commit()

    assert verify_password(new_password, user.hashed_password)


async def test_delete_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    user_id = user.id
    await delete_user(db, user)
    await db.commit()

    deleted = await get_user_by_id(db, user_id)
    assert deleted is None


async def test_authenticate_success(db: AsyncSession) -> None:
    """Test successful authentication."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    await create_user(db, user_in)
    await db.commit()

    authenticated_user = await authenticate(session=db, email=email, password=password)

    assert authenticated_user is not None
    assert authenticated_user.email == email


async def test_authenticate_wrong_password(db: AsyncSession) -> None:
    """Test authentication failure with wrong password."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    await create_user(db, user_in)
    await db.commit()

    authenticated_user = await authenticate(
        session=db, email=email, password="wrong_password"
    )

    assert authenticated_user is None


async def test_authenticate_nonexistent_user(db: AsyncSession) -> None:
    """Test authentication failure with nonexistent user."""
    authenticated_user = await authenticate(
        session=db, email="nonexistent@example.com", password="any_password"
    )

    assert authenticated_user is None


async def test_authenticate_empty_password(db: AsyncSession) -> None:
    """Test authentication failure with empty password."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    await create_user(db, user_in)
    await db.commit()

    authenticated_user = await authenticate(session=db, email=email, password="")

    assert authenticated_user is None


async def test_create_inactive_user(db: AsyncSession) -> None:
    """Test creating an inactive user."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)

    user = await create_user(db, user_in)
    await db.commit()

    assert user.is_active is False


async def test_update_user_is_superuser(db: AsyncSession) -> None:
    """Test updating a user to superuser."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    assert user.is_superuser is False

    user_update = UserUpdate(is_superuser=True)
    updated = await update_user(db, user, user_update)
    await db.commit()

    assert updated.is_superuser is True


async def test_update_user_is_active(db: AsyncSession) -> None:
    """Test updating user active status."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()

    assert user.is_active is True

    user_update = UserUpdate(is_active=False)
    updated = await update_user(db, user, user_update)
    await db.commit()

    assert updated.is_active is False


async def test_get_users_empty_database(db: AsyncSession) -> None:
    """Test getting user list from empty database."""
    # Note: init_db in conftest creates a superuser, so it's never truly empty
    users, count = await get_users(db, skip=0, limit=100)

    # At least one superuser should exist
    assert count >= 1
    assert len(users) >= 1


async def test_get_users_skip_beyond_count(db: AsyncSession) -> None:
    """Test that skip beyond total count returns an empty list."""
    users, count = await get_users(db, skip=1000, limit=100)

    assert users == []
    # count still returns the total
    assert count >= 0
