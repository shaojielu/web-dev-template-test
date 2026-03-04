import datetime
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.customers import CustomerCreate
from app.services.customer import create_customer

pytestmark = pytest.mark.anyio


async def test_update_invoice_change_customer(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test updating an invoice to a different customer."""
    customer1 = await create_customer(
        db,
        CustomerCreate(
            name=f"OldCustomer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    customer2 = await create_customer(
        db,
        CustomerCreate(
            name=f"NewCustomer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    create_resp = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(customer1.id),
            "amount": "50.00",
            "status": "pending",
            "date": str(datetime.date.today()),
        },
    )
    assert create_resp.status_code == 201
    invoice_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
        json={"customer_id": str(customer2.id)},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["customer_id"] == str(customer2.id)
    assert updated["name"] == customer2.name


async def test_update_invoice_change_to_nonexistent_customer(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test updating invoice customer_id to nonexistent customer returns 404."""
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"ExistingCust-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    create_resp = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(customer.id),
            "amount": "30.00",
            "status": "paid",
            "date": str(datetime.date.today()),
        },
    )
    assert create_resp.status_code == 201
    invoice_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
        json={"customer_id": str(uuid.uuid4())},
    )
    assert update_resp.status_code == 404
    assert update_resp.json()["detail"] == "Customer not found"


async def test_read_single_invoice(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    """Test GET /invoices/{id} returns correct invoice details."""
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Single-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    create_resp = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(customer.id),
            "amount": "77.77",
            "status": "pending",
            "date": str(datetime.date.today()),
        },
    )
    invoice_id = create_resp.json()["id"]

    resp = await client.get(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == "77.77"
    assert data["name"] == customer.name
    assert data["email"] == customer.email


async def test_read_single_invoice_not_found(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    resp = await client.get(
        f"{settings.API_V1_STR}/invoices/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Invoice not found"
