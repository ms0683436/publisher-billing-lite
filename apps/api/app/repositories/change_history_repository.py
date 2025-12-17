from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import ChangeHistory


async def create_history_entry(
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: int,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any],
    changed_by_user_id: int,
) -> ChangeHistory:
    """Create a new change history entry.

    Args:
        session: Database session
        entity_type: Type of entity (invoice_line_item, campaign, line_item, comment)
        entity_id: ID of the modified entity
        old_value: Previous field values (None for creation)
        new_value: New field values after the change
        changed_by_user_id: User ID who made the change

    Returns:
        Created ChangeHistory entry
    """
    entry = ChangeHistory(
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        changed_by_user_id=changed_by_user_id,
    )
    session.add(entry)
    await session.flush()
    return entry


async def create_history_entries_batch(
    session: AsyncSession,
    entries: list[dict[str, Any]],
) -> list[ChangeHistory]:
    """Create multiple change history entries in a batch.

    Args:
        session: Database session
        entries: List of dicts with keys: entity_type, entity_id, old_value,
                 new_value, changed_by_user_id

    Returns:
        List of created ChangeHistory entries
    """
    history_entries = [ChangeHistory(**entry) for entry in entries]
    session.add_all(history_entries)
    await session.flush()
    return history_entries


async def list_history_for_entity(
    session: AsyncSession,
    entity_type: str,
    entity_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChangeHistory], int]:
    """List change history for a specific entity.

    Args:
        session: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        Tuple of (history entries, total count)
    """
    # Count total
    count_stmt = select(func.count(ChangeHistory.id)).where(
        ChangeHistory.entity_type == entity_type,
        ChangeHistory.entity_id == entity_id,
    )
    total = (await session.execute(count_stmt)).scalar_one()

    # Get entries with user info
    stmt = (
        select(ChangeHistory)
        .where(
            ChangeHistory.entity_type == entity_type,
            ChangeHistory.entity_id == entity_id,
        )
        .options(selectinload(ChangeHistory.changed_by))
        .order_by(ChangeHistory.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    entries = list((await session.execute(stmt)).scalars().all())

    return entries, total


async def list_history_for_entities(
    session: AsyncSession,
    entity_type: str,
    entity_ids: list[int],
    *,
    limit: int = 100,
) -> list[ChangeHistory]:
    """List change history for multiple entities of the same type.

    Args:
        session: Database session
        entity_type: Type of entity
        entity_ids: List of entity IDs
        limit: Maximum number of entries to return

    Returns:
        List of history entries ordered by created_at desc
    """
    stmt = (
        select(ChangeHistory)
        .where(
            ChangeHistory.entity_type == entity_type,
            ChangeHistory.entity_id.in_(entity_ids),
        )
        .options(selectinload(ChangeHistory.changed_by))
        .order_by(ChangeHistory.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())
