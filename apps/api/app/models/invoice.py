from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .campaign import Campaign
    from .invoice_line_item import InvoiceLineItem


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        # Challenge simplification: enforce 1 campaign : 1 invoice
        UniqueConstraint("campaign_id", name="uq_invoices_campaign_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    campaign: Mapped[Campaign] = relationship(back_populates="invoice")
    invoice_line_items: Mapped[list[InvoiceLineItem]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
