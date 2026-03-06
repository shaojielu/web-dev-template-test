# Backend Patterns

Annotated code examples from the project's backend. Follow these patterns exactly when adding new features.

## Base Model

Source: `backend/app/models/base.py`

Every model inherits from `Base`, which provides `id` (UUID), `created_at`, and `updated_at` automatically.

```python
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )
```

## Model Pattern

Source: `backend/app/models/customer.py`

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice  # Avoid circular imports

class Customer(Base):
    __tablename__ = "customers"  # Plural, snake_case

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship with TYPE_CHECKING guard
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
```

Key points:

- `from __future__ import annotations` enables string-based type hints
- `TYPE_CHECKING` guard prevents circular imports between related models
- `Mapped[str | None]` for optional fields, `Mapped[str]` for required
- String columns need explicit `String(length)`

## Model with Foreign Key

Source: `backend/app/models/invoice.py`

```python
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), index=True, nullable=False  # References tablename, not class
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)

    customer: Mapped["Customer"] = relationship(back_populates="invoices")
```

Key points:

- `ForeignKey("customers.id")` uses the **table name** string, not the model class
- `Numeric(12, 2)` for monetary amounts
- `default="pending"` for Python-level defaults
- Index foreign key columns and frequently queried fields

## Model Registry

Source: `backend/app/models/__init__.py`

```python
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.user import User

__all__ = ["Customer", "Invoice", "User"]
```

Every new model **must** be imported here for Alembic autogenerate to detect it.

## Schema Pattern

Source: `backend/app/schemas/customers.py`

```python
from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema

# Base: shared fields with validation
class CustomerBase(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr = Field(max_length=100)
    image_url: str | None = Field(default=None, max_length=255)

# Create: inherits all Base fields (add extra creation-only fields if needed)
class CustomerCreate(CustomerBase):
    pass

# Update: all fields optional (for PATCH semantics)
class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=255)

# Public: response model with ID and timestamps
class CustomerPublic(CustomerBase, BaseSchema):
    id: uuid.UUID
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

# List response: data + count for pagination
class CustomersPublic(BaseSchema):
    data: list[CustomerPublic]
    count: int
```

Key points:

- `BaseSchema` (from `schemas/base.py`) adds `model_config = ConfigDict(from_attributes=True)` for ORM mode
- `Update` schemas inherit from `BaseModel` directly (not `Base`) with all fields optional
- `Public` schemas inherit from both `Base` schema and `BaseSchema`
- List responses always include `data` and `count`

## Service Pattern

Source: `backend/app/services/customer.py`

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.schemas.customers import CustomerCreate, CustomerUpdate

# CREATE: construct model, add to session, flush (not commit)
async def create_customer(session: AsyncSession, customer_in: CustomerCreate) -> Customer:
    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
    )
    session.add(customer)
    await session.flush()  # NOT commit - deps.py handles commit
    return customer

# READ by ID
async def get_customer_by_id(session: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
    return await session.get(Customer, customer_id)

# READ list with pagination
async def get_customers(
    session: AsyncSession, *, skip: int = 0, limit: int = 100
) -> tuple[list[Customer], int]:
    count_stmt = select(func.count()).select_from(Customer)
    total = await session.execute(count_stmt)
    count = total.scalar() or 0

    stmt = select(Customer).offset(skip).limit(limit).order_by(Customer.name)
    result = await session.execute(stmt)
    return list(result.scalars().all()), count

# UPDATE: use model_dump(exclude_unset=True) for partial updates
async def update_customer(
    session: AsyncSession, customer: Customer, customer_in: CustomerUpdate
) -> Customer:
    update_data = customer_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
    await session.flush()
    await session.refresh(customer)
    return customer

# DELETE
async def delete_customer(session: AsyncSession, customer: Customer) -> None:
    await session.delete(customer)
    await session.flush()
```

Key points:

- First parameter is always `session: AsyncSession`
- Use `flush()` after mutations, never `commit()`
- Pagination returns `tuple[list[Model], int]`
- Use `select()` + `session.execute()` (async 2.0 style), not `session.query()` (sync style)
- Use `model_dump(exclude_unset=True)` for partial updates to only apply fields that were sent

## Route Pattern

Source: `backend/app/api/routes/customers.py`

```python
from fastapi import APIRouter, Query
from app.api.deps import CurrentActiveUserDep, SessionDep
from app.schemas.customers import CustomersPublic, CustomerPublic
from app.services.customer import get_customers

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/", response_model=CustomersPublic)
async def read_customers(
    session: SessionDep,              # Injected DB session
    _: CurrentActiveUserDep,          # Auth guard (underscore = unused but enforced)
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> CustomersPublic:
    customers, count = await get_customers(session, skip=skip, limit=limit)
    return CustomersPublic(
        data=[CustomerPublic.model_validate(customer) for customer in customers],
        count=count,
    )
```

Key points:

- `router = APIRouter(prefix="/resource", tags=["resource"])`
- Inject `SessionDep` and `CurrentActiveUserDep` (or `CurrentUserDep`) in every protected route
- Use `_: CurrentActiveUserDep` when the user object isn't needed but auth is required
- Use `Query()` with `ge`/`le` for pagination validation
- Call service functions, convert to schema with `model_validate()`, return schema

## Dependency Injection

Source: `backend/app/api/deps.py`

Available dependencies (import from `app.api.deps`):

| Dependency             | Type           | Purpose                                 |
| ---------------------- | -------------- | --------------------------------------- |
| `SessionDep`           | `AsyncSession` | Database session (auto commit/rollback) |
| `CurrentUserDep`       | `User`         | Authenticated user (any status)         |
| `CurrentActiveUserDep` | `User`         | Authenticated + active user             |

```python
# Session lifecycle (from deps.py):
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()    # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise

SessionDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
```

Use `CurrentActiveUserDep` for most routes. Use `CurrentUserDep` only when inactive users should have access.
