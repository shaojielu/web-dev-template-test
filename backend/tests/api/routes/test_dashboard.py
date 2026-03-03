import datetime
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.invoice import Invoice
from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.services.customer import create_customer
from app.services.invoice import create_invoice

pytestmark = pytest.mark.anyio


async def test_read_dashboard_cards_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/dashboard/cards")
    assert response.status_code == 401


async def test_read_dashboard_revenue_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/dashboard/revenue")
    assert response.status_code == 401


async def test_read_dashboard_cards(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Dashboard-Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("15.00"),
            status="paid",
            date=datetime.date.today(),
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("7.00"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    response = await client.get(
        f"{settings.API_V1_STR}/dashboard/cards",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["number_of_invoices"] >= 2
    assert payload["number_of_customers"] >= 1
    assert isinstance(payload["total_paid_invoices"], str)
    assert isinstance(payload["total_pending_invoices"], str)


async def test_read_dashboard_revenue(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Revenue-Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("20.00"),
            status="paid",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    response = await client.get(
        f"{settings.API_V1_STR}/dashboard/revenue",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 12
    assert all("month" in item and "revenue" in item for item in payload)


async def test_read_dashboard_revenue_empty_data_returns_zeros(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    await db.execute(delete(Invoice))
    await db.commit()

    response = await client.get(
        f"{settings.API_V1_STR}/dashboard/revenue",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 12
    assert all(item["revenue"] == 0 for item in payload)
