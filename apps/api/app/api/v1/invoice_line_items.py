from fastapi import APIRouter, HTTPException

from ...api.deps import SessionDep
from ...schemas.invoice_line_item import InvoiceLineItemResponse, InvoiceLineItemUpdate
from ...services import NotFoundError, invoice_line_item_service

router = APIRouter(tags=["invoice-line-items"])


@router.patch(
    "/invoice-line-items/{invoice_line_item_id}",
    response_model=InvoiceLineItemResponse,
)
async def patch_invoice_line_item(
    invoice_line_item_id: int,
    payload: InvoiceLineItemUpdate,
    session: SessionDep,
):
    try:
        return await invoice_line_item_service.update_adjustments(
            session,
            invoice_line_item_id=invoice_line_item_id,
            adjustments=payload.adjustments,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        # Defensive: parse_money_2dp could raise if value is malformed.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
