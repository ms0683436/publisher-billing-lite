"""Helper functions for enqueueing change history tasks."""

from __future__ import annotations

import logging
from typing import Any

from .procrastinate_app import get_procrastinate_app

logger = logging.getLogger(__name__)


async def enqueue_change_history(
    *,
    entity_type: str,
    entity_id: int,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any],
    changed_by_user_id: int,
) -> bool:
    """Enqueue a single change history recording task.

    Args:
        entity_type: Type of entity (e.g., "comment", "invoice_line_item")
        entity_id: ID of the modified entity
        old_value: Previous field values
        new_value: New field values
        changed_by_user_id: User who made the change

    Returns:
        True if enqueued successfully, False otherwise
    """
    # Skip if no actual changes
    if old_value == new_value:
        return True

    try:
        app = get_procrastinate_app()
        # Lock by entity to ensure changes to the same entity are processed sequentially
        await app.configure_task(
            "change_history.record_change",
            lock=f"{entity_type}-{entity_id}",
        ).defer_async(
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            changed_by_user_id=changed_by_user_id,
        )
        logger.debug("Enqueued change history task for %s[%d]", entity_type, entity_id)
        return True
    except Exception as e:
        logger.warning("Failed to enqueue change history task: %s", e)
        return False


async def enqueue_change_history_batch(
    *,
    entity_type: str,
    changes: list[tuple[int, dict[str, Any] | None, dict[str, Any]]],
    changed_by_user_id: int,
) -> bool:
    """Enqueue change history recording tasks for multiple entities.

    Each entity change is enqueued as a separate job with a lock to ensure
    changes to the same entity are processed sequentially, even with concurrent workers.

    Args:
        entity_type: Type of entity (e.g., "comment", "invoice_line_item")
        changes: List of (entity_id, old_value, new_value) tuples
        changed_by_user_id: User who made the changes

    Returns:
        True if all enqueued successfully, False if any failed
    """
    # Filter out non-changes
    filtered_changes = [
        (entity_id, old_value, new_value)
        for entity_id, old_value, new_value in changes
        if old_value != new_value
    ]

    if not filtered_changes:
        return True

    try:
        app = get_procrastinate_app()

        # Enqueue each change as a separate job with entity-specific lock
        for entity_id, old_value, new_value in filtered_changes:
            await app.configure_task(
                "change_history.record_change",
                lock=f"{entity_type}-{entity_id}",
            ).defer_async(
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                changed_by_user_id=changed_by_user_id,
            )

        logger.debug(
            "Enqueued %d change history tasks for %s",
            len(filtered_changes),
            entity_type,
        )
        return True
    except Exception as e:
        logger.warning("Failed to enqueue change history tasks: %s", e)
        return False
