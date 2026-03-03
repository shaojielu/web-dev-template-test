import datetime
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.schemas.invoices import InvoiceCreate, InvoiceUpdate

CENT = Decimal("0.01")


async def create_invoice(session: AsyncSession, invoice_in: InvoiceCreate) -> Invoice:
    invoice = Invoice(
        customer_id=invoice_in.customer_id,
        amount=invoice_in.amount.quantize(CENT, rounding=ROUND_HALF_UP),
        status=invoice_in.status,
        date=invoice_in.date or datetime.date.today(),
    )
    session.add(invoice)
    await session.flush()
    return invoice


async def get_invoice_by_id(
    session: AsyncSession, invoice_id: uuid.UUID
) -> Invoice | None:
    return await session.get(Invoice, invoice_id)


async def get_invoice_with_customer(
    session: AsyncSession, invoice_id: uuid.UUID
) -> tuple[Invoice, Customer] | None:
    stmt = (
        select(Invoice, Customer)
        .join(Customer, Invoice.customer_id == Customer.id)
        .where(Invoice.id == invoice_id)
    )
    result = await session.execute(stmt)
    return result.tuples().one_or_none()


async def get_latest_invoices(
    session: AsyncSession, *, limit: int = 5
) -> list[tuple[Invoice, Customer]]:
    stmt = (
        select(Invoice, Customer)
        .join(Customer, Invoice.customer_id == Customer.id)
        .order_by(Invoice.date.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.tuples().all())


async def get_invoices(
    session: AsyncSession,
    *,
    query: str | None = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[tuple[Invoice, Customer]], int]:
    filters = []
    if query:
        search = f"%{query}%"
        filters.append(
            or_(
                Customer.name.ilike(search),
                Customer.email.ilike(search),
                cast(Invoice.amount, String).ilike(search),
                Invoice.status.ilike(search),
            )
        )

    count_stmt = select(func.count(Invoice.id)).join(
        Customer, Invoice.customer_id == Customer.id
    )
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = await session.execute(count_stmt)
    count = total.scalar() or 0

    stmt = select(Invoice, Customer).join(Customer, Invoice.customer_id == Customer.id)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Invoice.date.desc()).offset(skip).limit(limit)

    result = await session.execute(stmt)
    return list(result.tuples().all()), int(count)


async def update_invoice(
    session: AsyncSession, invoice: Invoice, invoice_in: InvoiceUpdate
) -> Invoice:
    update_data = invoice_in.model_dump(exclude_unset=True)
    if "amount" in update_data and update_data["amount"] is not None:
        update_data["amount"] = update_data["amount"].quantize(
            CENT, rounding=ROUND_HALF_UP
        )
    for key, value in update_data.items():
        setattr(invoice, key, value)
    await session.flush()
    await session.refresh(invoice)
    return invoice


async def delete_invoice(session: AsyncSession, invoice: Invoice) -> None:
    await session.delete(invoice)
    await session.flush()


async def count_invoices(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Invoice)
    result = await session.execute(stmt)
    return int(result.scalar() or 0)
