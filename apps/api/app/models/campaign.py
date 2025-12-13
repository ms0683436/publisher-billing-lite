from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .invoice import Invoice
    from .line_item import LineItem


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    line_items: Mapped[list[LineItem]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    invoice: Mapped[Invoice | None] = relationship(
        back_populates="campaign",
        uselist=False,
        cascade="all, delete-orphan",
    )
