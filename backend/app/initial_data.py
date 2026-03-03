import asyncio
import datetime
import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session
from app.schemas.customers import CustomerCreate
from app.schemas.invoices import InvoiceCreate
from app.schemas.users import UserCreate
from app.services.customer import (
    count_customers,
    create_customer,
    default_avatar_url,
    get_customers,
)
from app.services.invoice import count_invoices, create_invoice
from app.services.user import create_user, get_user_by_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    user = await get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        await create_user(session, user_in)

    if not settings.SEED_SAMPLE_DATA:
        await session.commit()
        return

    if await count_customers(session) == 0:
        sample_customers = [
            CustomerCreate(
                name="Alice Johnson",
                email="alice@example.com",
                image_url=default_avatar_url("alice@example.com"),
            ),
            CustomerCreate(
                name="Bob Smith",
                email="bob@example.com",
                image_url=default_avatar_url("bob@example.com"),
            ),
            CustomerCreate(
                name="Carla Gomez",
                email="carla@example.com",
                image_url=default_avatar_url("carla@example.com"),
            ),
            CustomerCreate(
                name="Derek Lee",
                email="derek@example.com",
                image_url=default_avatar_url("derek@example.com"),
            ),
            CustomerCreate(
                name="Evelyn Chen",
                email="evelyn@example.com",
                image_url=default_avatar_url("evelyn@example.com"),
            ),
            CustomerCreate(
                name="Fatima Noor",
                email="fatima@example.com",
                image_url=default_avatar_url("fatima@example.com"),
            ),
        ]
        for customer_in in sample_customers:
            await create_customer(session, customer_in)

    if await count_invoices(session) == 0:
        customers, _ = await get_customers(session, skip=0, limit=50)
        if customers:
            today = datetime.date.today()
            sample_invoices = [
                InvoiceCreate(
                    customer_id=customers[0].id,
                    amount=Decimal("320.25"),
                    status="paid",
                    date=today - datetime.timedelta(days=7),
                ),
                InvoiceCreate(
                    customer_id=customers[1].id,
                    amount=Decimal("128.00"),
                    status="pending",
                    date=today - datetime.timedelta(days=14),
                ),
                InvoiceCreate(
                    customer_id=customers[2].id,
                    amount=Decimal("540.50"),
                    status="paid",
                    date=today - datetime.timedelta(days=25),
                ),
                InvoiceCreate(
                    customer_id=customers[3].id,
                    amount=Decimal("75.00"),
                    status="pending",
                    date=today - datetime.timedelta(days=33),
                ),
                InvoiceCreate(
                    customer_id=customers[4].id,
                    amount=Decimal("890.99"),
                    status="paid",
                    date=today - datetime.timedelta(days=45),
                ),
                InvoiceCreate(
                    customer_id=customers[5].id,
                    amount=Decimal("210.00"),
                    status="paid",
                    date=today - datetime.timedelta(days=60),
                ),
                InvoiceCreate(
                    customer_id=customers[0].id,
                    amount=Decimal("150.75"),
                    status="pending",
                    date=today - datetime.timedelta(days=75),
                ),
                InvoiceCreate(
                    customer_id=customers[1].id,
                    amount=Decimal("430.40"),
                    status="paid",
                    date=today - datetime.timedelta(days=90),
                ),
            ]
            for invoice_in in sample_invoices:
                await create_invoice(session, invoice_in)

    await session.commit()


async def main() -> None:
    logger.info("Creating initial data")
    async with async_session() as session:
        await init_db(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
