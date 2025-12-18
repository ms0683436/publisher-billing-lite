from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .user import User


class Notification(Base):
    """User notification for @mentions and other events."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Recipient of the notification
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification type: "mention" or "reply"
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="mention",
    )

    # Human-readable message
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Read status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Related comment
    comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        index=True,
    )

    # Actor who triggered the notification
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    # Only created_at (notifications are immutable, no index needed)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    actor: Mapped[User | None] = relationship(foreign_keys=[actor_id])
    comment: Mapped[Comment | None] = relationship()
