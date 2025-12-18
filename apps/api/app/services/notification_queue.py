"""Notification queue using Redis for async notification processing."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis

from ..settings import get_settings

logger = logging.getLogger(__name__)

NOTIFICATION_QUEUE_KEY = "notification_queue"


class TaskType(str, Enum):
    """Types of notification tasks."""

    MENTION = "mention"
    REPLY = "reply"


@dataclass
class NotificationTask:
    """A notification task to be processed by the worker."""

    task_type: TaskType
    # For MENTION tasks
    mentioned_user_ids: list[int] | None = None
    author_id: int | None = None
    comment_id: int | None = None
    # For REPLY tasks
    parent_comment_id: int | None = None
    reply_author_id: int | None = None
    reply_comment_id: int | None = None

    def to_json(self) -> str:
        """Serialize task to JSON."""
        return json.dumps(
            {
                "task_type": self.task_type.value,
                "mentioned_user_ids": self.mentioned_user_ids,
                "author_id": self.author_id,
                "comment_id": self.comment_id,
                "parent_comment_id": self.parent_comment_id,
                "reply_author_id": self.reply_author_id,
                "reply_comment_id": self.reply_comment_id,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> NotificationTask:
        """Deserialize task from JSON."""
        parsed = json.loads(data)
        return cls(
            task_type=TaskType(parsed["task_type"]),
            mentioned_user_ids=parsed.get("mentioned_user_ids"),
            author_id=parsed.get("author_id"),
            comment_id=parsed.get("comment_id"),
            parent_comment_id=parsed.get("parent_comment_id"),
            reply_author_id=parsed.get("reply_author_id"),
            reply_comment_id=parsed.get("reply_comment_id"),
        )


class NotificationQueue:
    """Redis-based notification queue for async processing.

    Uses Redis List (LPUSH/BRPOP) as a simple, reliable queue.
    """

    def __init__(self, redis_url: str) -> None:
        """Initialize the queue with Redis connection.

        Args:
            redis_url: Redis connection URL
        """
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def enqueue(self, task: NotificationTask) -> bool:
        """Add a notification task to the queue.

        Args:
            task: The notification task to enqueue

        Returns:
            True if enqueued successfully, False otherwise
        """
        try:
            client = await self._get_redis()
            await client.lpush(NOTIFICATION_QUEUE_KEY, task.to_json())  # type: ignore[misc]
            logger.debug("Enqueued notification task: %s", task.task_type.value)
            return True
        except redis.RedisError as e:
            logger.warning("Failed to enqueue notification task: %s", e)
            return False

    async def dequeue(self, timeout: float = 5.0) -> NotificationTask | None:
        """Remove and return a task from the queue.

        Blocks until a task is available or timeout is reached.

        Args:
            timeout: Seconds to wait for a task (0 = block forever)

        Returns:
            NotificationTask if available, None on timeout
        """
        try:
            client = await self._get_redis()
            result = await client.brpop(  # type: ignore[misc]
                [NOTIFICATION_QUEUE_KEY], timeout=timeout
            )
            if result is None:
                return None
            # result is (key, value) tuple
            _, task_json = result
            return NotificationTask.from_json(task_json)
        except redis.RedisError as e:
            logger.error("Failed to dequeue notification task: %s", e)
            return None

    async def get_queue_length(self) -> int:
        """Get the current number of tasks in the queue."""
        try:
            client = await self._get_redis()
            return await client.llen(NOTIFICATION_QUEUE_KEY)  # type: ignore[misc]
        except redis.RedisError:
            return 0


# Global queue instance
_queue: NotificationQueue | None = None


def get_notification_queue() -> NotificationQueue:
    """Get the global notification queue instance."""
    global _queue
    if _queue is None:
        settings = get_settings()
        _queue = NotificationQueue(settings.redis_url)
    return _queue


async def shutdown_notification_queue() -> None:
    """Shutdown the global queue instance."""
    global _queue
    if _queue is not None:
        await _queue.close()
        _queue = None


# Helper functions for enqueuing specific task types


async def enqueue_mention_notifications(
    mentioned_user_ids: list[int],
    author_id: int,
    comment_id: int,
) -> bool:
    """Enqueue a mention notification task.

    Args:
        mentioned_user_ids: List of user IDs to notify
        author_id: User who created the comment
        comment_id: The comment containing mentions

    Returns:
        True if enqueued successfully
    """
    if not mentioned_user_ids:
        return True

    queue = get_notification_queue()
    task = NotificationTask(
        task_type=TaskType.MENTION,
        mentioned_user_ids=mentioned_user_ids,
        author_id=author_id,
        comment_id=comment_id,
    )
    return await queue.enqueue(task)


async def enqueue_reply_notification(
    parent_comment_id: int,
    reply_author_id: int,
    reply_comment_id: int,
) -> bool:
    """Enqueue a reply notification task.

    Args:
        parent_comment_id: The comment being replied to
        reply_author_id: User who created the reply
        reply_comment_id: The reply comment

    Returns:
        True if enqueued successfully
    """
    queue = get_notification_queue()
    task = NotificationTask(
        task_type=TaskType.REPLY,
        parent_comment_id=parent_comment_id,
        reply_author_id=reply_author_id,
        reply_comment_id=reply_comment_id,
    )
    return await queue.enqueue(task)
