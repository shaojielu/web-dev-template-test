import datetime
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.services.customer import (
    create_customer,
    default_avatar_url,
    get_customer_summaries,
    normalize_image_url,
)
from app.services.invoice import create_invoice

pytestmark = pytest.mark.anyio


async def test_normalize_image_url_preserves_external_url() -> None:
    image_url = "https://example.com/avatar.png"
    normalized = normalize_image_url(image_url, "seed@example.com")
    assert normalized == image_url


async def test_normalize_image_url_falls_back_for_empty_value() -> None:
    seed = "fallback@example.com"
    normalized = normalize_image_url(None, seed)
    assert normalized == default_avatar_url(seed)


async def test_get_customer_summaries_formats_decimal_totals(db: AsyncSession) -> None:
    tag = str(uuid.uuid4())
    customer = await create_customer(
        db,
        CustomerCreate(
            name=f"Summary-{tag}",
            email=f"{tag}@example.com",
            image_url=None,
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
            amount=Decimal("3.75"),
            status="pending",
            date=datetime.date.today(),
        ),
    )
    await db.commit()

    data, count = await get_customer_summaries(db, query=f"Summary-{tag}", skip=0, limit=10)
    assert count == 1
    assert len(data) == 1
    assert data[0]["total_paid"] == "12.50"
    assert data[0]["total_pending"] == "3.75"
