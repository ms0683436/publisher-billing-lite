from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import InvoiceLineItem


async def get_invoice_line_item(
    session: AsyncSession, invoice_line_item_id: int, *, for_update: bool = False
) -> InvoiceLineItem | None:
    stmt = select(InvoiceLineItem).where(InvoiceLineItem.id == invoice_line_item_id)
    if for_update:
        stmt = stmt.with_for_update()
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_invoice_line_item_adjustments(
    session: AsyncSession,
    invoice_line_item_id: int,
    *,
    adjustments: Decimal,
    for_update: bool = False,
) -> InvoiceLineItem | None:
    """Update adjustments for an invoice line item.

    Repository responsibility: persistence only.
    Validation (e.g. allowed range/format) should live in services.
    """

    invoice_line_item = await get_invoice_line_item(
        session, invoice_line_item_id, for_update=for_update
    )
    if invoice_line_item is None:
        return None

    invoice_line_item.adjustments = adjustments
    await session.flush()
    # updated_at is server-side; refresh to avoid implicit IO on attribute access
    # which can raise sqlalchemy.exc.MissingGreenlet under async.
    await session.refresh(invoice_line_item)
    return invoice_line_item
