from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .invoice import Invoice
    from .line_item import LineItem


class InvoiceLineItem(Base, TimestampMixin):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            "line_item_id",
            name="uq_invoice_line_items_invoice_id_line_item_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_item_id: Mapped[int] = mapped_column(
        ForeignKey("line_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=30, scale=15, asdecimal=True),
        nullable=False,
        server_default=sa.text("0"),
    )
    adjustments: Mapped[Decimal] = mapped_column(
        Numeric(precision=30, scale=15, asdecimal=True),
        nullable=False,
        server_default=sa.text("0"),
    )

    invoice: Mapped[Invoice] = relationship(back_populates="invoice_line_items")
    line_item: Mapped[LineItem] = relationship(back_populates="invoice_line_items")
