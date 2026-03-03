import datetime
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.services.customer import create_customer
from app.services.invoice import create_invoice

pytestmark = pytest.mark.anyio


async def test_read_customers_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/customers/")
    assert response.status_code == 401


async def test_read_customers_summary_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/customers/summary")
    assert response.status_code == 401


async def test_read_customers_with_pagination(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    await create_customer(
        db,
        CustomerCreate(
            name=f"Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await create_customer(
        db,
        CustomerCreate(
            name=f"Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    response = await client.get(
        f"{settings.API_V1_STR}/customers/?skip=0&limit=1",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 2
    assert len(payload["data"]) == 1


async def test_read_customers_limit_boundary(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/customers/?skip=0&limit=500",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


async def test_read_customers_limit_out_of_range(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/customers/?skip=0&limit=501",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422


async def test_read_customers_summary_with_search(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Searchable-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url="https://example.com/avatar.png",
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("12.50"),
            status="paid",
            date=datetime.date.today(),
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("5.00"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    response = await client.get(
        f"{settings.API_V1_STR}/customers/summary?query=Searchable",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    item = payload["data"][0]
    assert item["name"].startswith("Searchable-")
    assert item["total_paid"] == "12.50"
    assert item["total_pending"] == "5.00"


async def test_read_customers_summary_empty_result(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/customers/summary?query=no-such-customer",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["data"] == []
