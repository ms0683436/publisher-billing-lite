"""Change history recording tasks for async processing."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ...repositories import change_history_repository
from ...settings import get_settings
from ..procrastinate_app import get_procrastinate_app

logger = logging.getLogger(__name__)

# Session maker for worker (separate from API process)
_session_maker: async_sessionmaker[AsyncSession] | None = None


def _get_worker_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create session maker for worker process."""
    global _session_maker
    if _session_maker is None:
        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


app = get_procrastinate_app()


@app.task(name="change_history.record_change", retry=3)
async def record_change_task(
    entity_type: str,
    entity_id: int,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any],
    changed_by_user_id: int,
) -> None:
    """Record a single change history entry asynchronously.

    Args:
        entity_type: Type of entity (invoice_line_item, comment, etc.)
        entity_id: ID of the modified entity
        old_value: Previous field values (None for creation)
        new_value: New field values
        changed_by_user_id: User who made the change
    """
    # Skip if no actual changes
    if old_value == new_value:
        logger.debug("Skipping change history - no changes detected")
        return

    session_maker = _get_worker_session_maker()
    async with session_maker() as session:
        await change_history_repository.create_history_entry(
            session,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            changed_by_user_id=changed_by_user_id,
        )
        await session.commit()

    logger.info(
        "Recorded change history: %s[%d] by user %d",
        entity_type,
        entity_id,
        changed_by_user_id,
    )
