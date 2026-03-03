"""add invoice status constraints and indexes

Revision ID: 8a7c03f98c62
Revises: 1c6e1c955af4
Create Date: 2026-02-12 16:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a7c03f98c62"
down_revision: Union[str, Sequence[str], None] = "1c6e1c955af4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_invoices_status_valid",
        "invoices",
        "status IN ('pending', 'paid')",
    )
    op.create_index("ix_invoices_date", "invoices", ["date"], unique=False)
    op.create_index("ix_invoices_status", "invoices", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_date", table_name="invoices")
    op.drop_constraint("ck_invoices_status_valid", "invoices", type_="check")
