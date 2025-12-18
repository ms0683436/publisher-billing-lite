"""Notification repository - data access layer for notifications."""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Notification


async def create_notification(
    session: AsyncSession,
    *,
    user_id: int,
    notification_type: str,
    message: str,
    comment_id: int | None = None,
    actor_id: int | None = None,
) -> Notification:
    """Create a new notification.

    Args:
        session: Database session
        user_id: Recipient user ID
        notification_type: Notification type (e.g., "mention", "reply")
        message: Human-readable message
        comment_id: Related comment ID (optional)
        actor_id: User who triggered the notification (optional)

    Returns:
        Created notification
    """
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        comment_id=comment_id,
        actor_id=actor_id,
    )
    session.add(notification)
    await session.flush()
    return notification


async def create_notifications_batch(
    session: AsyncSession,
    notifications_data: list[dict],
) -> list[Notification]:
    """Create multiple notifications in batch.

    Args:
        session: Database session
        notifications_data: List of notification dicts with keys:
            user_id, type, message, comment_id (optional), actor_id (optional)

    Returns:
        List of created notifications
    """
    notifications = [Notification(**data) for data in notifications_data]
    session.add_all(notifications)
    await session.flush()
    return notifications


async def list_notifications_for_user(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 5,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    """List notifications for a user.

    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of notifications
        offset: Number of notifications to skip

    Returns:
        Tuple of (notifications list, total count)
    """
    # Count total
    count_stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id
    )
    total = (await session.execute(count_stmt)).scalar_one()

    # Get notifications with relationships
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.comment),
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    notifications = list((await session.execute(stmt)).scalars().all())

    return notifications, total


async def count_unread_notifications(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Count unread notifications for a user.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Number of unread notifications
    """
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        ~Notification.is_read,
    )
    return (await session.execute(stmt)).scalar_one()


async def get_notification(
    session: AsyncSession,
    notification_id: int,
) -> Notification | None:
    """Get a notification by ID.

    Args:
        session: Database session
        notification_id: Notification ID

    Returns:
        Notification instance or None
    """
    stmt = (
        select(Notification)
        .where(Notification.id == notification_id)
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.comment),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def mark_notification_as_read(
    session: AsyncSession,
    notification_id: int,
) -> None:
    """Mark a single notification as read.

    Args:
        session: Database session
        notification_id: Notification ID
    """
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id)
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.flush()


async def mark_all_notifications_as_read(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Mark all notifications for a user as read.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Number of notifications marked as read
    """
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            ~Notification.is_read,
        )
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount or 0  # type: ignore[attr-defined]
