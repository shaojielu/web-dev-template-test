import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.initial_data import init_db
from app.services.customer import count_customers
from app.services.invoice import count_invoices

pytestmark = pytest.mark.anyio


async def test_init_db_seeds_sample_data_when_enabled(db: AsyncSession) -> None:
    """Test that init_db creates sample customers and invoices when SEED_SAMPLE_DATA=True."""
    original = settings.SEED_SAMPLE_DATA
    settings.SEED_SAMPLE_DATA = True
    try:
        await init_db(db)

        customer_count = await count_customers(db)
        invoice_count = await count_invoices(db)
        assert customer_count >= 6
        assert invoice_count >= 8
    finally:
        settings.SEED_SAMPLE_DATA = original


async def test_init_db_skips_seeding_when_disabled(db: AsyncSession) -> None:
    """Test that init_db does not seed when SEED_SAMPLE_DATA=False."""
    original = settings.SEED_SAMPLE_DATA
    settings.SEED_SAMPLE_DATA = False
    try:
        customer_before = await count_customers(db)
        await init_db(db)
        customer_after = await count_customers(db)
        assert customer_after == customer_before
    finally:
        settings.SEED_SAMPLE_DATA = original
