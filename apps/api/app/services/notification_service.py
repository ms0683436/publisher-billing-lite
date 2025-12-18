"""Notification service with business logic for creating and managing notifications."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import notification_repository
from ..schemas.notification import (
    NotificationListResponse,
    NotificationReadResponse,
    NotificationResponse,
)
from .errors import ForbiddenError, NotFoundError

if TYPE_CHECKING:
    from ..models import Comment, Notification, User

logger = logging.getLogger(__name__)


def _notification_to_response(notification: Notification) -> NotificationResponse:
    """Convert Notification model to NotificationResponse schema."""
    return NotificationResponse.model_validate(notification)


async def create_mention_notifications(
    session: AsyncSession,
    *,
    mentioned_users: list[User],
    author: User,
    comment: Comment,
) -> list[Notification]:
    """Create notifications for all users mentioned in a comment.

    Excludes self-mentions (author mentioning themselves).

    Args:
        session: Database session
        mentioned_users: List of users who were mentioned
        author: User who created the comment
        comment: The comment containing the mentions

    Returns:
        List of created notifications
    """
    notifications_to_create = []

    for user in mentioned_users:
        # Don't notify users who mention themselves
        if user.id == author.id:
            continue

        notifications_to_create.append(
            {
                "user_id": user.id,
                "type": "mention",
                "message": f"@{author.username} mentioned you in a comment",
                "comment_id": comment.id,
                "actor_id": author.id,
            }
        )

    if not notifications_to_create:
        return []

    notifications = await notification_repository.create_notifications_batch(
        session, notifications_to_create
    )

    logger.info(
        "Created %d mention notifications for comment %d",
        len(notifications),
        comment.id,
    )

    return notifications


async def create_reply_notification(
    session: AsyncSession,
    *,
    parent_comment: Comment,
    reply_author: User,
    reply_comment: Comment,
) -> Notification | None:
    """Create a notification for the parent comment author when someone replies.

    Args:
        session: Database session
        parent_comment: The comment being replied to
        reply_author: User who created the reply
        reply_comment: The reply comment

    Returns:
        Created notification or None if author replies to themselves
    """
    # Don't notify if replying to own comment
    if parent_comment.author_id == reply_author.id:
        return None

    notification = await notification_repository.create_notification(
        session,
        user_id=parent_comment.author_id,
        notification_type="reply",
        message=f"@{reply_author.username} replied to your comment",
        comment_id=reply_comment.id,
        actor_id=reply_author.id,
    )

    logger.info(
        "Created reply notification for user %d from comment %d",
        parent_comment.author_id,
        reply_comment.id,
    )

    return notification


async def list_notifications(
    session: AsyncSession,
    *,
    user_id: int,
    limit: int = 5,
    offset: int = 0,
) -> NotificationListResponse:
    """List notifications for the current user.

    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of notifications
        offset: Number of notifications to skip

    Returns:
        NotificationListResponse with notifications, total, and unread_count
    """
    notifications, total = await notification_repository.list_notifications_for_user(
        session, user_id, limit=limit, offset=offset
    )
    unread_count = await notification_repository.count_unread_notifications(
        session, user_id
    )

    return NotificationListResponse(
        notifications=[_notification_to_response(n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


async def mark_as_read(
    session: AsyncSession,
    *,
    notification_id: int,
    current_user_id: int,
) -> NotificationReadResponse:
    """Mark a single notification as read.

    Args:
        session: Database session
        notification_id: Notification ID
        current_user_id: Current user's ID

    Returns:
        NotificationReadResponse

    Raises:
        NotFoundError: If notification not found
        ForbiddenError: If notification belongs to another user
    """
    notification = await notification_repository.get_notification(
        session, notification_id
    )

    if notification is None:
        raise NotFoundError("notification", notification_id)

    if notification.user_id != current_user_id:
        raise ForbiddenError("mark as read", "notification")

    await notification_repository.mark_notification_as_read(session, notification_id)
    await session.commit()

    return NotificationReadResponse(success=True, read_count=1)


async def mark_all_as_read(
    session: AsyncSession,
    *,
    current_user_id: int,
) -> NotificationReadResponse:
    """Mark all notifications for the current user as read.

    Args:
        session: Database session
        current_user_id: Current user's ID

    Returns:
        NotificationReadResponse with count of notifications marked
    """
    count = await notification_repository.mark_all_notifications_as_read(
        session, current_user_id
    )
    await session.commit()

    return NotificationReadResponse(success=True, read_count=count)
