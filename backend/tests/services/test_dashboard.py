import calendar
import datetime
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.services.customer import create_customer
from app.services.dashboard import get_dashboard_cards, get_revenue_last_12_months
from app.services.invoice import create_invoice

pytestmark = pytest.mark.anyio


async def test_get_dashboard_cards_returns_string_totals(db: AsyncSession) -> None:
    await db.execute(delete(Invoice))
    await db.commit()

    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Cards-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("10.00"),
            status="paid",
            date=datetime.date.today(),
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("4.50"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    cards = await get_dashboard_cards(db)
    assert cards.number_of_invoices >= 2
    assert cards.number_of_customers >= 1
    assert cards.total_paid_invoices == "10.00"
    assert cards.total_pending_invoices == "4.50"


async def test_get_revenue_last_12_months_empty_returns_zeros(db: AsyncSession) -> None:
    await db.execute(delete(Invoice))
    await db.commit()

    revenue = await get_revenue_last_12_months(db)
    assert len(revenue) == 12
    assert all(item.revenue == 0 for item in revenue)


async def test_get_revenue_last_12_months_aggregates_current_month(
    db: AsyncSession,
) -> None:
    await db.execute(delete(Invoice))
    await db.commit()

    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Revenue-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@example.com",
            image_url=None,
        ),
    )
    today = datetime.date.today()
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("7.25"),
            status="paid",
            date=today,
        ),
    )
    await create_invoice(
        db,
        InvoiceCreate(
            customer_id=customer.id,
            amount=Decimal("2.75"),
            status="pending",
            date=today,
        ),
    )
    await db.commit()

    revenue = await get_revenue_last_12_months(db)
    current_month = calendar.month_abbr[today.month]
    current_point = next(item for item in revenue if item.month == current_month)
    assert current_point.revenue == 10.0
