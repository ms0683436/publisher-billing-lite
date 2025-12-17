from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class ChangeHistory(Base):
    """Audit log for tracking changes to editable entities.

    Records changes as JSONB objects containing only the modified fields.
    Example:
        old_value: {"adjustments": "100.00"}
        new_value: {"adjustments": "150.00"}
    """

    __tablename__ = "change_history"
    __table_args__ = (Index("ix_change_history_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Entity type: invoice_line_item, campaign, line_item, comment",
    )

    entity_id: Mapped[int] = mapped_column(
        nullable=False,
        comment="ID of the modified entity",
    )

    old_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Previous values (null for creation)",
    )

    new_value: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="New values after the change",
    )

    changed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    changed_by: Mapped[User] = relationship(foreign_keys=[changed_by_user_id])
