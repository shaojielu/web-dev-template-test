from __future__ import annotations

import datetime  # noqa: TC003
import uuid  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class Invoice(Base):
    __tablename__ = "invoices"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)

    customer: Mapped["Customer"] = relationship(back_populates="invoices")  # noqa: UP037
