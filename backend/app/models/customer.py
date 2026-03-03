from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class Customer(Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    invoices: Mapped[list["Invoice"]] = relationship(  # noqa: UP037
        back_populates="customer", cascade="all, delete-orphan"
    )
