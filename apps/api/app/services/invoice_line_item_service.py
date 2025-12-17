from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import InvoiceLineItem
from ..repositories import invoice_line_item_repository
from ..schemas.invoice_line_item import (
    BatchAdjustmentsResponse,
    InvoiceLineItemResponse,
)
from . import change_history_service
from .change_history_service import EntityType
from .money import parse_money_2dp


class BatchUpdateError(Exception):
    """Raised when batch update fails validation."""

    def __init__(self, message: str, invalid_ids: list[int] | None = None):
        super().__init__(message)
        self.invalid_ids = invalid_ids or []


async def batch_update_adjustments(
    session: AsyncSession,
    *,
    invoice_id: int,
    updates: list[tuple[int, str]],
    current_user_id: int,
) -> BatchAdjustmentsResponse:
    """Batch update adjustments for multiple invoice line items.

    All-or-nothing: if any validation fails, the entire batch is rejected.
    Records change history for each modified item.
    """
    # Parse and validate all adjustments first
    parsed_updates: list[tuple[int, Decimal]] = []
    for ili_id, adj_str in updates:
        try:
            adj_dec = parse_money_2dp(adj_str)
            parsed_updates.append((ili_id, adj_dec))
        except ValueError as e:
            raise BatchUpdateError(
                f"Invalid adjustment for invoice_line_item_id {ili_id}: {e}",
                invalid_ids=[ili_id],
            ) from e

    # Get current values before update (for change history)
    ids = [u[0] for u in parsed_updates]
    stmt = select(InvoiceLineItem).where(
        InvoiceLineItem.id.in_(ids),
        InvoiceLineItem.invoice_id == invoice_id,
    )
    result = await session.execute(stmt)
    old_items = {ili.id: ili.adjustments for ili in result.scalars().all()}

    # Perform batch update
    updated_items = await invoice_line_item_repository.batch_update_adjustments(
        session,
        invoice_id=invoice_id,
        updates=parsed_updates,
        for_update=True,
    )

    if not updated_items:
        raise BatchUpdateError(
            f"One or more invoice_line_item_ids not found "
            f"or do not belong to invoice {invoice_id}"
        )

    # Record change history for items that actually changed (store raw values)
    changes: list[tuple[int, dict | None, dict]] = []
    for ili in updated_items:
        old_adj = old_items.get(ili.id)
        if old_adj is not None and old_adj != ili.adjustments:
            changes.append(
                (
                    ili.id,
                    {"adjustments": str(old_adj)},
                    {"adjustments": str(ili.adjustments)},
                )
            )

    if changes:
        await change_history_service.record_changes_batch(
            session,
            entity_type=EntityType.INVOICE_LINE_ITEM,
            changes=changes,
            changed_by_user_id=current_user_id,
        )

    await session.commit()

    return BatchAdjustmentsResponse(
        invoice_id=invoice_id,
        updated=[
            InvoiceLineItemResponse(
                id=ili.id,
                invoice_id=ili.invoice_id,
                line_item_id=ili.line_item_id,
                actual_amount=ili.actual_amount,
                adjustments=ili.adjustments,
                updated_at=ili.updated_at,
            )
            for ili in updated_items
        ],
    )
