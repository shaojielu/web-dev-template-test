import datetime
import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema


class CustomerBase(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr = Field(max_length=100)
    image_url: str | None = Field(default=None, max_length=255)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=255)


class CustomerPublic(CustomerBase, BaseSchema):
    id: uuid.UUID
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class CustomersPublic(BaseSchema):
    data: list[CustomerPublic]
    count: int


class CustomerSummary(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    image_url: str | None
    total_invoices: int
    total_pending: str
    total_paid: str


class CustomersSummary(BaseModel):
    data: list[CustomerSummary]
    count: int
