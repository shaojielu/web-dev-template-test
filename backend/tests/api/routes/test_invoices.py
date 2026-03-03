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


async def test_read_invoices_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/invoices/")
    assert response.status_code == 401


async def test_write_invoices_requires_auth(client: AsyncClient) -> None:
    invoice_id = str(uuid.uuid4())

    create_response = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        json={
            "customer_id": str(uuid.uuid4()),
            "amount": "10.00",
            "status": "pending",
            "date": str(datetime.date.today()),
        },
    )
    assert create_response.status_code == 401

    patch_response = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        json={"status": "paid"},
    )
    assert patch_response.status_code == 401

    delete_response = await client.delete(
        f"{settings.API_V1_STR}/invoices/{invoice_id}"
    )
    assert delete_response.status_code == 401


async def test_invoice_crud_flow(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Invoice-Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    create_payload = {
        "customer_id": str(customer.id),
        "amount": "120.50",
        "status": "pending",
        "date": str(datetime.date.today()),
    }
    create_response = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json=create_payload,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    invoice_id = created["id"]
    assert created["amount"] == "120.50"
    assert created["status"] == "pending"

    read_response = await client.get(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
    )
    assert read_response.status_code == 200
    assert read_response.json()["id"] == invoice_id

    update_response = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
        json={"amount": "200.00", "status": "paid"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["amount"] == "200.00"
    assert updated["status"] == "paid"

    list_response = await client.get(
        f"{settings.API_V1_STR}/invoices/?query=200.00",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["count"] >= 1
    assert any(item["id"] == invoice_id for item in list_payload["data"])

    delete_response = await client.delete(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Invoice deleted"

    read_after_delete = await client.get(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
    )
    assert read_after_delete.status_code == 404


async def test_create_invoice_customer_not_found(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(uuid.uuid4()),
            "amount": "10.00",
            "status": "pending",
            "date": str(datetime.date.today()),
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


async def test_update_invoice_partial_fields(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Partial-Update-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    create_response = await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(customer.id),
            "amount": "19.90",
            "status": "pending",
            "date": str(datetime.date.today()),
        },
    )
    assert create_response.status_code == 201
    invoice_id = create_response.json()["id"]

    status_only_response = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
        json={"status": "paid"},
    )
    assert status_only_response.status_code == 200
    assert status_only_response.json()["status"] == "paid"
    assert status_only_response.json()["amount"] == "19.90"

    amount_only_response = await client.patch(
        f"{settings.API_V1_STR}/invoices/{invoice_id}",
        headers=superuser_token_headers,
        json={"amount": "22.00"},
    )
    assert amount_only_response.status_code == 200
    assert amount_only_response.json()["amount"] == "22.00"
    assert amount_only_response.json()["status"] == "paid"


async def test_create_invoice_invalid_amount_returns_422(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Invalid-Amount-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    for invalid_amount in ("0", "10.999", "1234567890123.45"):
        response = await client.post(
            f"{settings.API_V1_STR}/invoices/",
            headers=superuser_token_headers,
            json={
                "customer_id": str(customer.id),
                "amount": invalid_amount,
                "status": "pending",
                "date": str(datetime.date.today()),
            },
        )
        assert response.status_code == 422


async def test_update_delete_invoice_not_found(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
) -> None:
    missing_invoice_id = str(uuid.uuid4())

    patch_response = await client.patch(
        f"{settings.API_V1_STR}/invoices/{missing_invoice_id}",
        headers=superuser_token_headers,
        json={"amount": str(Decimal("99.99"))},
    )
    assert patch_response.status_code == 404

    delete_response = await client.delete(
        f"{settings.API_V1_STR}/invoices/{missing_invoice_id}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 404


async def test_read_latest_invoices(
    client: AsyncClient,
    db: AsyncSession,
    superuser_token_headers: dict[str, str],
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Latest-Customer-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.commit()

    await client.post(
        f"{settings.API_V1_STR}/invoices/",
        headers=superuser_token_headers,
        json={
            "customer_id": str(customer.id),
            "amount": "88.00",
            "status": "paid",
            "date": str(datetime.date.today()),
        },
    )

    response = await client.get(
        f"{settings.API_V1_STR}/invoices/latest",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
