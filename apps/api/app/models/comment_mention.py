from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .comment import Comment
    from .user import User


class CommentMention(Base, TimestampMixin):
    __tablename__ = "comment_mentions"
    __table_args__ = (
        UniqueConstraint(
            "comment_id", "user_id", name="uq_comment_mentions_comment_user"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    comment: Mapped[Comment] = relationship(back_populates="mentions")
    user: Mapped[User] = relationship()
