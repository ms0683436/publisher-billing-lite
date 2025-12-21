"""Unit tests for notification broadcaster."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis

from app.services.notification_broadcaster import (
    NotificationBroadcaster,
    get_broadcaster,
    shutdown_broadcaster,
)


class TestNotificationBroadcasterInit:
    """Tests for NotificationBroadcaster initialization."""

    def test_init_sets_redis_url(self):
        """Init stores redis_url and sets redis to None."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")

        assert broadcaster._redis_url == "redis://localhost:6379"
        assert broadcaster._redis is None


class TestNotificationBroadcasterGetRedis:
    """Tests for _get_redis lazy connection."""

    @pytest.mark.asyncio
    async def test_get_redis_creates_connection(self):
        """First call to _get_redis creates connection."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")

        with patch.object(redis, "from_url") as mock_from_url:
            mock_redis = MagicMock()
            mock_from_url.return_value = mock_redis

            result = await broadcaster._get_redis()

            mock_from_url.assert_called_once_with(
                "redis://localhost:6379", decode_responses=True
            )
            assert result is mock_redis
            assert broadcaster._redis is mock_redis

    @pytest.mark.asyncio
    async def test_get_redis_reuses_connection(self):
        """Subsequent calls reuse existing connection."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")
        mock_redis = MagicMock()
        broadcaster._redis = mock_redis

        with patch.object(redis, "from_url") as mock_from_url:
            result = await broadcaster._get_redis()

            mock_from_url.assert_not_called()
            assert result is mock_redis


class TestNotificationBroadcasterClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_clears_connection(self):
        """Close calls redis.close and clears reference."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")
        mock_redis = AsyncMock()
        broadcaster._redis = mock_redis

        await broadcaster.close()

        mock_redis.close.assert_called_once()
        assert broadcaster._redis is None

    @pytest.mark.asyncio
    async def test_close_noop_when_no_connection(self):
        """Close is safe when no connection exists."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")

        # Should not raise
        await broadcaster.close()
        assert broadcaster._redis is None


class TestNotificationBroadcasterPublish:
    """Tests for publish method."""

    @pytest.mark.asyncio
    async def test_publish_sends_to_channel(self):
        """Publish sends JSON to user channel."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")
        mock_redis = AsyncMock()
        broadcaster._redis = mock_redis

        await broadcaster.publish(42, {"type": "mention", "id": 123})

        mock_redis.publish.assert_called_once_with(
            "notifications:42", '{"type": "mention", "id": 123}'
        )

    @pytest.mark.asyncio
    async def test_publish_handles_redis_error(self):
        """Publish catches RedisError and logs warning."""
        broadcaster = NotificationBroadcaster("redis://localhost:6379")
        mock_redis = AsyncMock()
        mock_redis.publish.side_effect = redis.RedisError("Connection refused")
        broadcaster._redis = mock_redis

        # Should not raise - fails silently
        await broadcaster.publish(42, {"type": "mention"})


class TestGlobalBroadcaster:
    """Tests for global broadcaster functions."""

    def test_get_broadcaster_creates_singleton(self):
        """get_broadcaster creates and returns singleton."""
        import app.services.notification_broadcaster as module

        # Reset global
        module._broadcaster = None

        with patch.object(module, "get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://test:6379"
            broadcaster = get_broadcaster()

            assert broadcaster is not None
            assert isinstance(broadcaster, NotificationBroadcaster)
            assert broadcaster._redis_url == "redis://test:6379"

            # Second call returns same instance
            broadcaster2 = get_broadcaster()
            assert broadcaster2 is broadcaster

        # Cleanup
        module._broadcaster = None

    @pytest.mark.asyncio
    async def test_shutdown_broadcaster_cleans_up(self):
        """shutdown_broadcaster closes and clears global."""
        import app.services.notification_broadcaster as module

        mock_broadcaster = AsyncMock()
        module._broadcaster = mock_broadcaster

        await shutdown_broadcaster()

        mock_broadcaster.close.assert_called_once()
        assert module._broadcaster is None

    @pytest.mark.asyncio
    async def test_shutdown_broadcaster_noop_when_none(self):
        """shutdown_broadcaster is safe when no broadcaster exists."""
        import app.services.notification_broadcaster as module

        module._broadcaster = None

        # Should not raise
        await shutdown_broadcaster()
        assert module._broadcaster is None
