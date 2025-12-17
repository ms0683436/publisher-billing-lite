from __future__ import annotations

from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import change_history_repository
from ..schemas.change_history import ChangeHistoryListResponse, ChangeHistoryResponse


class EntityType(str, Enum):
    """Supported entity types for change history tracking."""

    INVOICE_LINE_ITEM = "invoice_line_item"
    CAMPAIGN = "campaign"
    LINE_ITEM = "line_item"
    COMMENT = "comment"


async def record_change(
    session: AsyncSession,
    *,
    entity_type: EntityType,
    entity_id: int,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any],
    changed_by_user_id: int,
) -> None:
    """Record a change to an entity.

    Only records if there are actual changes (old_value != new_value).

    Args:
        session: Database session
        entity_type: Type of entity being changed
        entity_id: ID of the entity
        old_value: Previous field values (None for creation)
        new_value: New field values
        changed_by_user_id: User ID who made the change
    """
    # Skip if no actual changes
    if old_value == new_value:
        return

    await change_history_repository.create_history_entry(
        session,
        entity_type=entity_type.value,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        changed_by_user_id=changed_by_user_id,
    )


async def record_changes_batch(
    session: AsyncSession,
    *,
    entity_type: EntityType,
    changes: list[tuple[int, dict[str, Any] | None, dict[str, Any]]],
    changed_by_user_id: int,
) -> None:
    """Record multiple changes in a batch.

    Args:
        session: Database session
        entity_type: Type of entity being changed
        changes: List of (entity_id, old_value, new_value) tuples
        changed_by_user_id: User ID who made the changes
    """
    # Filter out non-changes
    entries = [
        {
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "old_value": old_value,
            "new_value": new_value,
            "changed_by_user_id": changed_by_user_id,
        }
        for entity_id, old_value, new_value in changes
        if old_value != new_value
    ]

    if entries:
        await change_history_repository.create_history_entries_batch(session, entries)


async def get_history_for_entity(
    session: AsyncSession,
    entity_type: EntityType,
    entity_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
) -> ChangeHistoryListResponse:
    """Get change history for a specific entity.

    Args:
        session: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        ChangeHistoryListResponse with history entries and total count
    """
    entries, total = await change_history_repository.list_history_for_entity(
        session,
        entity_type.value,
        entity_id,
        limit=limit,
        offset=offset,
    )

    return ChangeHistoryListResponse(
        history=[
            ChangeHistoryResponse(
                id=entry.id,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                old_value=entry.old_value,
                new_value=entry.new_value,
                changed_by_user_id=entry.changed_by_user_id,
                changed_by_username=entry.changed_by.username,
                created_at=entry.created_at,
            )
            for entry in entries
        ],
        total=total,
    )
