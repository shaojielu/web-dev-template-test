import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.customers import CustomerCreate, CustomerUpdate
from app.services.customer import (
    count_customers,
    create_customer,
    delete_customer,
    get_customer_by_email,
    get_customer_by_id,
    get_customers,
    normalize_image_url,
    update_customer,
)

pytestmark = pytest.mark.anyio


async def test_get_customer_by_id(db: AsyncSession) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name="ById-Test",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    found = await get_customer_by_id(db, customer.id)
    assert found is not None
    assert found.id == customer.id


async def test_get_customer_by_id_not_found(db: AsyncSession) -> None:
    found = await get_customer_by_id(db, uuid.uuid4())
    assert found is None


async def test_get_customer_by_email(db: AsyncSession) -> None:
    email = f"{uuid.uuid4()}@example.com"
    await create_customer(
        db,
        CustomerCreate(name="ByEmail-Test", email=email, image_url=None),
    )
    await db.commit()

    found = await get_customer_by_email(db, email)
    assert found is not None
    assert found.email == email


async def test_get_customer_by_email_not_found(db: AsyncSession) -> None:
    found = await get_customer_by_email(db, "does-not-exist@example.com")
    assert found is None


async def test_get_customers_pagination(db: AsyncSession) -> None:
    for i in range(3):
        await create_customer(
            db,
            CustomerCreate(
                name=f"Page-{i}-{uuid.uuid4()}",
                email=f"{uuid.uuid4()}@example.com",
                image_url=None,
            ),
        )
    await db.commit()

    customers, count = await get_customers(db, skip=0, limit=2)
    assert count >= 3
    assert len(customers) == 2


async def test_update_customer(db: AsyncSession) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name="Original",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    updated = await update_customer(
        db, customer, CustomerUpdate(name="Updated")
    )
    await db.commit()

    assert updated.name == "Updated"


async def test_delete_customer(db: AsyncSession) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name="ToDelete",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()
    customer_id = customer.id

    await delete_customer(db, customer)
    await db.commit()

    assert await get_customer_by_id(db, customer_id) is None


async def test_count_customers(db: AsyncSession) -> None:
    initial = await count_customers(db)
    await create_customer(
        db,
        CustomerCreate(
            name="Count-Test",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    assert await count_customers(db) == initial + 1


def test_normalize_image_url_with_relative_path() -> None:
    assert normalize_image_url("/avatar.png", "seed") == "/avatar.png"


def test_normalize_image_url_with_http() -> None:
    url = "http://example.com/img.png"
    assert normalize_image_url(url, "seed") == url


def test_normalize_image_url_with_invalid_value() -> None:
    result = normalize_image_url("not-a-url", "seed")
    assert result.startswith("/customers/")
