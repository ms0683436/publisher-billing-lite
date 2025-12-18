"""Notification worker that processes the notification queue.

This worker runs as a separate process, polling the Redis queue
and creating/broadcasting notifications asynchronously.

Usage:
    python -m app.workers.notification_worker
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..repositories import comment_repository, notification_repository, user_repository
from ..schemas.notification import NotificationResponse
from ..services import notification_service
from ..services.notification_broadcaster import get_broadcaster, shutdown_broadcaster
from ..services.notification_queue import (
    NotificationTask,
    TaskType,
    get_notification_queue,
    shutdown_notification_queue,
)
from ..settings import get_settings

if TYPE_CHECKING:
    from ..models import Notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NotificationWorker:
    """Worker that processes notification tasks from the queue."""

    def __init__(self) -> None:
        """Initialize the worker."""
        self._running = False
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def setup(self) -> None:
        """Set up database connection and other resources."""
        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self._session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Worker setup complete")

    @asynccontextmanager
    async def get_session(self):
        """Get a database session."""
        if self._session_maker is None:
            raise RuntimeError("Worker not set up")
        async with self._session_maker() as session:
            yield session

    async def process_mention_task(
        self, session: AsyncSession, task: NotificationTask
    ) -> None:
        """Process a mention notification task."""
        if not task.mentioned_user_ids or not task.author_id or not task.comment_id:
            logger.warning("Invalid mention task: missing required fields")
            return

        # Get author and comment
        author = await user_repository.get_user(session, task.author_id)
        if author is None:
            logger.warning("Author %d not found, skipping task", task.author_id)
            return

        comment = await comment_repository.get_comment(session, task.comment_id)
        if comment is None:
            logger.warning("Comment %d not found, skipping task", task.comment_id)
            return

        # Get mentioned users
        mentioned_users = []
        for user_id in task.mentioned_user_ids:
            user = await user_repository.get_user(session, user_id)
            if user is not None:
                mentioned_users.append(user)

        if not mentioned_users:
            logger.debug("No valid mentioned users found")
            return

        # Create notifications
        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=mentioned_users,
            author=author,
            comment=comment,
        )
        await session.commit()

        # Broadcast notifications
        await self._broadcast_notifications(session, notifications)

        logger.info(
            "Processed mention task: %d notifications for comment %d",
            len(notifications),
            task.comment_id,
        )

    async def process_reply_task(
        self, session: AsyncSession, task: NotificationTask
    ) -> None:
        """Process a reply notification task."""
        if (
            not task.parent_comment_id
            or not task.reply_author_id
            or not task.reply_comment_id
        ):
            logger.warning("Invalid reply task: missing required fields")
            return

        # Get parent comment, reply author, and reply comment
        parent_comment = await comment_repository.get_comment(
            session, task.parent_comment_id
        )
        if parent_comment is None:
            logger.warning(
                "Parent comment %d not found, skipping task", task.parent_comment_id
            )
            return

        reply_author = await user_repository.get_user(session, task.reply_author_id)
        if reply_author is None:
            logger.warning(
                "Reply author %d not found, skipping task", task.reply_author_id
            )
            return

        reply_comment = await comment_repository.get_comment(
            session, task.reply_comment_id
        )
        if reply_comment is None:
            logger.warning(
                "Reply comment %d not found, skipping task", task.reply_comment_id
            )
            return

        # Create reply notification
        notification = await notification_service.create_reply_notification(
            session,
            parent_comment=parent_comment,
            reply_author=reply_author,
            reply_comment=reply_comment,
        )
        await session.commit()

        if notification is not None:
            await self._broadcast_notifications(session, [notification])
            logger.info(
                "Processed reply task: notification for comment %d",
                task.reply_comment_id,
            )

    async def _broadcast_notifications(
        self, session: AsyncSession, notifications: list[Notification]
    ) -> None:
        """Broadcast notifications via Redis Pub/Sub.

        Re-fetches each notification to ensure relationships (actor, comment)
        are loaded before serializing for broadcast.
        """
        broadcaster = get_broadcaster()
        for notification in notifications:
            # Re-fetch with relationships loaded for complete payload
            loaded = await notification_repository.get_notification(
                session, notification.id
            )
            if loaded is None:
                continue
            notification_data = NotificationResponse.model_validate(loaded).model_dump(
                mode="json"
            )
            await broadcaster.publish(loaded.user_id, notification_data)

    async def process_task(self, task: NotificationTask) -> None:
        """Process a single notification task."""
        async with self.get_session() as session:
            if task.task_type == TaskType.MENTION:
                await self.process_mention_task(session, task)
            elif task.task_type == TaskType.REPLY:
                await self.process_reply_task(session, task)
            else:
                logger.warning("Unknown task type: %s", task.task_type)

    async def run(self) -> None:
        """Run the worker loop."""
        await self.setup()
        self._running = True

        queue = get_notification_queue()
        logger.info("Notification worker started, waiting for tasks...")

        while self._running:
            try:
                task = await queue.dequeue(timeout=5.0)
                if task is not None:
                    await self.process_task(task)
            except Exception as e:
                logger.exception("Error processing task: %s", e)
                # Continue processing other tasks

        logger.info("Notification worker stopped")

    def stop(self) -> None:
        """Signal the worker to stop."""
        logger.info("Stopping notification worker...")
        self._running = False


async def main() -> None:
    """Main entry point for the worker."""
    worker = NotificationWorker()

    # Handle shutdown signals
    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await worker.run()
    finally:
        await shutdown_notification_queue()
        await shutdown_broadcaster()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
