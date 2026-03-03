import uuid
from hashlib import sha256

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.schemas.customers import CustomerCreate, CustomerSummary, CustomerUpdate
from app.utils.utils import decimal_to_currency_string

_AVATAR_POOL = [
    "/customers/amy-burns.png",
    "/customers/balazs-orban.png",
    "/customers/delba-de-oliveira.png",
    "/customers/evil-rabbit.png",
    "/customers/lee-robinson.png",
    "/customers/michael-novotny.png",
]


def default_avatar_url(seed: str) -> str:
    digest = sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(_AVATAR_POOL)
    return _AVATAR_POOL[index]


def normalize_image_url(image_url: str | None, seed: str) -> str:
    if image_url and (
        image_url.startswith("/")
        or image_url.startswith("http://")
        or image_url.startswith("https://")
    ):
        return image_url
    return default_avatar_url(seed)


async def create_customer(
    session: AsyncSession, customer_in: CustomerCreate
) -> Customer:
    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
        image_url=normalize_image_url(customer_in.image_url, customer_in.email),
    )
    session.add(customer)
    await session.flush()
    return customer


async def get_customer_by_id(
    session: AsyncSession, customer_id: uuid.UUID
) -> Customer | None:
    return await session.get(Customer, customer_id)


async def get_customer_by_email(session: AsyncSession, email: str) -> Customer | None:
    stmt = select(Customer).where(Customer.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_customers(
    session: AsyncSession, *, skip: int = 0, limit: int = 100
) -> tuple[list[Customer], int]:
    count_stmt = select(func.count()).select_from(Customer)
    total = await session.execute(count_stmt)
    count = total.scalar() or 0

    stmt = select(Customer).offset(skip).limit(limit).order_by(Customer.name)
    result = await session.execute(stmt)
    return list(result.scalars().all()), count


async def get_customer_summaries(
    session: AsyncSession,
    *,
    query: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[CustomerSummary], int]:
    total_pending = func.coalesce(
        func.sum(case((Invoice.status == "pending", Invoice.amount), else_=0)), 0
    ).label("total_pending")
    total_paid = func.coalesce(
        func.sum(case((Invoice.status == "paid", Invoice.amount), else_=0)), 0
    ).label("total_paid")
    total_invoices = func.count(Invoice.id).label("total_invoices")

    filters = []
    if query:
        search = f"%{query}%"
        filters.append(or_(Customer.name.ilike(search), Customer.email.ilike(search)))

    count_stmt = select(func.count()).select_from(Customer)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = await session.execute(count_stmt)
    count = total.scalar() or 0

    stmt = (
        select(
            Customer.id,
            Customer.name,
            Customer.email,
            Customer.image_url,
            total_invoices,
            total_pending,
            total_paid,
        )
        .outerjoin(Invoice, Invoice.customer_id == Customer.id)
        .group_by(Customer.id)
        .order_by(Customer.name)
        .offset(skip)
        .limit(limit)
    )
    if filters:
        stmt = stmt.where(*filters)

    result = await session.execute(stmt)
    rows: list[CustomerSummary] = []
    for row in result.all():
        rows.append(
            CustomerSummary(
                id=row.id,
                name=row.name,
                email=row.email,
                image_url=normalize_image_url(row.image_url, row.email),
                total_invoices=int(row.total_invoices or 0),
                total_pending=decimal_to_currency_string(row.total_pending),
                total_paid=decimal_to_currency_string(row.total_paid),
            )
        )
    return rows, int(count)


async def update_customer(
    session: AsyncSession, customer: Customer, customer_in: CustomerUpdate
) -> Customer:
    update_data = customer_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
    await session.flush()
    await session.refresh(customer)
    return customer


async def delete_customer(session: AsyncSession, customer: Customer) -> None:
    await session.delete(customer)
    await session.flush()


async def count_customers(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Customer)
    result = await session.execute(stmt)
    return int(result.scalar() or 0)
