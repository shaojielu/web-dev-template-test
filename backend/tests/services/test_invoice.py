import datetime
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate, InvoiceUpdate
from app.services.customer import create_customer
from app.services.invoice import create_invoice, get_invoices, update_invoice

pytestmark = pytest.mark.anyio


async def test_create_invoice_quantizes_amount_and_sets_default_date(
    db: AsyncSession,
) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Create-Invoice-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    invoice = await create_invoice(
        db,
        InvoiceCreate(customer_id=customer.id, amount=Decimal("10.1"), status="pending"),
    )
    await db.commit()

    assert invoice.amount == Decimal("10.10")
    assert invoice.date == datetime.date.today()


async def test_get_invoices_query_and_pagination(db: AsyncSession) -> None:
    alpha_customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Alpha-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    beta_customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Beta-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=alpha_customer.id,
            amount=Decimal("20.00"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=beta_customer.id,
            amount=Decimal("30.00"),
            status="paid",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    filtered, filtered_count = await get_invoices(db, query="Alpha-", skip=0, limit=10)
    assert filtered_count == 1
    assert len(filtered) == 1
    assert filtered[0][1].name.startswith("Alpha-")

    paged, total_count = await get_invoices(db, skip=0, limit=1)
    assert total_count >= 2
    assert len(paged) == 1


async def test_update_invoice_quantizes_amount(db: AsyncSession) -> None:
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Update-Invoice-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    invoice = await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("19.90"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    updated = await update_invoice(
        db,
        invoice,
        InvoiceUpdate(amount=Decimal("21"), status="paid"),
    )
    await db.commit()

    assert updated.amount == Decimal("21.00")
    assert updated.status == "paid"
