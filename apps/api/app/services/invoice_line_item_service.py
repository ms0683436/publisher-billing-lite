from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import invoice_line_item_repository
from ..schemas.invoice_line_item import InvoiceLineItemResponse
from .errors import NotFoundError
from .money import parse_money_2dp


async def update_adjustments(
    session: AsyncSession,
    *,
    invoice_line_item_id: int,
    adjustments: str,
) -> InvoiceLineItemResponse:
    adjustments_dec = parse_money_2dp(adjustments)

    ili = await invoice_line_item_repository.update_invoice_line_item_adjustments(
        session,
        invoice_line_item_id,
        adjustments=adjustments_dec,
        for_update=True,
    )
    if ili is None:
        raise NotFoundError("invoice_line_item", invoice_line_item_id)

    await session.commit()

    return InvoiceLineItemResponse(
        id=ili.id,
        invoice_id=ili.invoice_id,
        line_item_id=ili.line_item_id,
        actual_amount=ili.actual_amount,
        adjustments=ili.adjustments,
        updated_at=ili.updated_at,
    )
