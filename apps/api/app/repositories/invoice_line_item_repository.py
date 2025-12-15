from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import InvoiceLineItem


async def batch_update_adjustments(
    session: AsyncSession,
    invoice_id: int,
    updates: list[tuple[int, Decimal]],
    *,
    for_update: bool = False,
) -> list[InvoiceLineItem]:
    """Batch update adjustments for multiple invoice line items.

    Args:
        session: Database session
        invoice_id: Invoice ID (for ownership validation)
        updates: List of (invoice_line_item_id, adjustments) tuples

    Returns:
        List of updated InvoiceLineItems.
        Empty list if any invoice_line_item_id not found or doesn't belong to invoice.
    """
    if not updates:
        return []

    ids = [u[0] for u in updates]
    stmt = select(InvoiceLineItem).where(
        InvoiceLineItem.id.in_(ids),
        InvoiceLineItem.invoice_id == invoice_id,
    )
    if for_update:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    items = {ili.id: ili for ili in result.scalars().all()}

    # Verify all IDs found and belong to invoice
    if len(items) != len(updates):
        return []

    # Apply updates
    updates_map = dict(updates)
    for ili_id, ili in items.items():
        ili.adjustments = updates_map[ili_id]

    await session.flush()

    # Refresh all to get updated_at
    for ili in items.values():
        await session.refresh(ili)

    return list(items.values())
