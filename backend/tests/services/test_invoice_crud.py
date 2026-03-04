import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.services.customer import create_customer
from app.services.invoice import (
    count_invoices,
    create_invoice,
    delete_invoice,
    get_invoice_by_id,
    get_invoice_with_customer,
    get_latest_invoices,
)

pytestmark = pytest.mark.anyio


async def _make_customer(db: AsyncSession) -> uuid.UUID:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Inv-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await db.flush()
    return customer.id


async def test_get_invoice_by_id(db: AsyncSession) -> None:
    cid = await _make_customer(db)
    invoice = await create_invoice(
        db,
        InvoiceCreate(customer_id=cid, amount=Decimal("50.00"), status="pending"),
    )
    await db.commit()

    found = await get_invoice_by_id(db, invoice.id)
    assert found is not None
    assert found.id == invoice.id


async def test_get_invoice_by_id_not_found(db: AsyncSession) -> None:
    found = await get_invoice_by_id(db, uuid.uuid4())
    assert found is None


async def test_get_invoice_with_customer(db: AsyncSession) -> None:
    cid = await _make_customer(db)
    invoice = await create_invoice(
        db,
        InvoiceCreate(customer_id=cid, amount=Decimal("25.00"), status="paid"),
    )
    await db.commit()

    result = await get_invoice_with_customer(db, invoice.id)
    assert result is not None
    inv, cust = result
    assert inv.id == invoice.id
    assert cust.id == cid


async def test_get_invoice_with_customer_not_found(db: AsyncSession) -> None:
    result = await get_invoice_with_customer(db, uuid.uuid4())
    assert result is None


async def test_get_latest_invoices(db: AsyncSession) -> None:
    cid = await _make_customer(db)
    for _ in range(3):
        await create_invoice(
            db,
            InvoiceCreate(customer_id=cid, amount=Decimal("10.00"), status="paid"),
        )
    await db.commit()

    latest = await get_latest_invoices(db, limit=2)
    assert len(latest) == 2
    for inv, cust in latest:
        assert cust.id == cid


async def test_delete_invoice(db: AsyncSession) -> None:
    cid = await _make_customer(db)
    invoice = await create_invoice(
        db,
        InvoiceCreate(customer_id=cid, amount=Decimal("5.00"), status="pending"),
    )
    await db.commit()
    invoice_id = invoice.id

    await delete_invoice(db, invoice)
    await db.commit()

    assert await get_invoice_by_id(db, invoice_id) is None


async def test_count_invoices(db: AsyncSession) -> None:
    cid = await _make_customer(db)
    initial = await count_invoices(db)
    await create_invoice(
        db,
        InvoiceCreate(customer_id=cid, amount=Decimal("1.00"), status="paid"),
    )
    await db.commit()

    assert await count_invoices(db) == initial + 1
