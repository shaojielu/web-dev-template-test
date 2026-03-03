import calendar
import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.utils.utils import decimal_to_currency_string


def _month_start(value: datetime.date, months_back: int) -> datetime.date:
    year = value.year
    month = value.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return datetime.date(year, month, 1)


def _add_months(value: datetime.date, months: int) -> datetime.date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return datetime.date(year, month, 1)


async def get_dashboard_cards(session: AsyncSession) -> dict[str, str | int]:
    invoices_stmt = select(func.count()).select_from(Invoice)
    customers_stmt = select(func.count()).select_from(Customer)
    paid_stmt = select(func.coalesce(func.sum(Invoice.amount), 0)).where(
        Invoice.status == "paid"
    )
    pending_stmt = select(func.coalesce(func.sum(Invoice.amount), 0)).where(
        Invoice.status == "pending"
    )

    invoices_result = await session.execute(invoices_stmt)
    customers_result = await session.execute(customers_stmt)
    paid_result = await session.execute(paid_stmt)
    pending_result = await session.execute(pending_stmt)

    return {
        "number_of_invoices": int(invoices_result.scalar() or 0),
        "number_of_customers": int(customers_result.scalar() or 0),
        "total_paid_invoices": decimal_to_currency_string(paid_result.scalar()),
        "total_pending_invoices": decimal_to_currency_string(
            pending_result.scalar()
        ),
    }


async def get_revenue_last_12_months(
    session: AsyncSession,
) -> list[dict[str, float | str]]:
    today = datetime.date.today()
    start = _month_start(today, 11)
    end = _add_months(start, 12)

    stmt = (
        select(Invoice.date, Invoice.amount)
        .where(Invoice.date >= start)
        .where(Invoice.date < end)
    )
    result = await session.execute(stmt)

    buckets: dict[tuple[int, int], float] = {}
    for invoice_date, amount in result.all():
        key = (invoice_date.year, invoice_date.month)
        buckets[key] = buckets.get(key, 0.0) + float(amount)

    revenue: list[dict[str, float | str]] = []
    current = start
    for _ in range(12):
        key = (current.year, current.month)
        revenue.append(
            {
                "month": calendar.month_abbr[current.month],
                "revenue": round(buckets.get(key, 0.0), 2),
            }
        )
        current = _add_months(current, 1)

    return revenue
