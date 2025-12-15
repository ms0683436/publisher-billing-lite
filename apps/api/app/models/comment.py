from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    from .campaign import Campaign
    from .comment_mention import CommentMention
    from .user import User


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Campaign relationship (only Campaign supported)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Author relationship
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nested replies (self-referential)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        index=True,
    )

    # Relationships
    author: Mapped[User] = relationship(back_populates="comments")
    campaign: Mapped[Campaign] = relationship(back_populates="comments")
    mentions: Mapped[list[CommentMention]] = relationship(
        back_populates="comment",
        cascade="all, delete-orphan",
    )

    # Nested replies relationships
    parent: Mapped[Comment | None] = relationship(
        back_populates="replies",
        remote_side=[id],
    )
    replies: Mapped[list[Comment]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
