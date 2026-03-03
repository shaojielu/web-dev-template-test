import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema

InvoiceStatus = Literal["pending", "paid"]


class InvoiceBase(BaseModel):
    customer_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    status: InvoiceStatus
    date: datetime.date


class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    status: InvoiceStatus
    date: datetime.date | None = None


class InvoiceUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    status: InvoiceStatus | None = None
    date: datetime.date | None = None


class InvoicePublic(BaseSchema):
    id: uuid.UUID
    customer_id: uuid.UUID
    amount: str
    status: InvoiceStatus
    date: datetime.date
    name: str
    email: str
    image_url: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class InvoicesPublic(BaseSchema):
    data: list[InvoicePublic]
    count: int
