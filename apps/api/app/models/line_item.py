from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .campaign import Campaign
    from .invoice_line_item import InvoiceLineItem


class LineItem(Base, TimestampMixin):
    __tablename__ = "line_items"
    __table_args__ = (
        UniqueConstraint("campaign_id", "name", name="uq_line_items_campaign_id_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    booked_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=30, scale=15, asdecimal=True),
        nullable=False,
        server_default=sa.text("0"),
    )

    campaign: Mapped[Campaign] = relationship(back_populates="line_items")
    invoice_line_items: Mapped[list[InvoiceLineItem]] = relationship(
        back_populates="line_item",
        cascade="all, delete-orphan",
    )
