"""Notification schemas for API request/response validation."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, field_serializer

from .base import BaseSchema
from .user import UserBase


class NotificationResponse(BaseSchema):
    """Single notification response."""

    id: int
    type: str
    message: str
    is_read: bool
    comment_id: int | None
    actor: UserBase | None
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def serialize_datetime_as_utc(self, value: datetime) -> str:
        """Serialize datetime as UTC with explicit timezone."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        else:
            value = value.astimezone(UTC)
        return value.isoformat()


class NotificationListResponse(BaseModel):
    """GET /api/v1/notifications response."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationReadResponse(BaseModel):
    """Response after marking notification(s) as read."""

    success: bool
    read_count: int
