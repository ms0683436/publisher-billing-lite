from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, field_serializer

from .base import BaseSchema


class ChangeHistoryResponse(BaseSchema):
    """Single change history entry response."""

    id: int
    entity_type: str
    entity_id: int
    old_value: dict[str, Any] | None
    new_value: dict[str, Any]
    changed_by_user_id: int
    changed_by_username: str
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def serialize_datetime_as_utc(self, value: datetime) -> str:
        """Serialize datetime as UTC with explicit timezone.

        Note: Only created_at is needed for audit logs (immutable records).
        Using same pattern as TimestampMixin for consistency.
        """
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        else:
            value = value.astimezone(UTC)
        return value.isoformat()


class ChangeHistoryListResponse(BaseModel):
    """Response for listing change history."""

    history: list[ChangeHistoryResponse]
    total: int
