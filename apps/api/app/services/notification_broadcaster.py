"""Notification broadcaster using Redis Pub/Sub for real-time notifications."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis

from ..settings import get_settings

logger = logging.getLogger(__name__)


class NotificationBroadcaster:
    """Redis Pub/Sub broadcaster for real-time notifications.

    Handles publishing notifications to user-specific channels and
    subscribing to receive real-time updates.
    """

    def __init__(self, redis_url: str) -> None:
        """Initialize the broadcaster with Redis connection.

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

    async def publish(self, user_id: int, notification: dict[str, Any]) -> None:
        """Publish a notification to a user's channel.

        Args:
            user_id: Target user ID
            notification: Notification data to publish

        Note:
            Fails silently if Redis is unavailable to prevent breaking
            the main application flow.
        """
        try:
            client = await self._get_redis()
            channel = f"notifications:{user_id}"
            message = json.dumps(notification)
            await client.publish(channel, message)
            logger.debug("Published notification to channel %s", channel)
        except redis.RedisError as e:
            logger.warning(
                "Failed to publish notification to Redis channel notifications:%s: %s",
                user_id,
                e,
            )

    @asynccontextmanager
    async def subscribe(self, user_id: int) -> AsyncIterator[AsyncIterator[dict]]:
        """Subscribe to a user's notification channel.

        Args:
            user_id: User ID to subscribe to

        Yields:
            Async iterator of notification dicts
        """
        client = await self._get_redis()
        pubsub = client.pubsub()
        channel = f"notifications:{user_id}"

        try:
            await pubsub.subscribe(channel)
            logger.debug("Subscribed to channel %s", channel)

            async def message_generator() -> AsyncIterator[dict]:
                """Generate notification messages from the channel."""
                while True:
                    try:
                        message = await asyncio.wait_for(
                            pubsub.get_message(ignore_subscribe_messages=True),
                            timeout=30.0,  # Heartbeat timeout
                        )
                        if message is not None and message["type"] == "message":
                            yield json.loads(message["data"])
                    except TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield {"type": "heartbeat"}

            yield message_generator()
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.debug("Unsubscribed from channel %s", channel)


# Global broadcaster instance
_broadcaster: NotificationBroadcaster | None = None


def get_broadcaster() -> NotificationBroadcaster:
    """Get the global broadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        settings = get_settings()
        _broadcaster = NotificationBroadcaster(settings.redis_url)
    return _broadcaster


async def shutdown_broadcaster() -> None:
    """Shutdown the global broadcaster instance."""
    global _broadcaster
    if _broadcaster is not None:
        await _broadcaster.close()
        _broadcaster = None
