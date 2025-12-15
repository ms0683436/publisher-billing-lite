from fastapi import APIRouter, HTTPException

from ...api.deps import PaginationDep, SessionDep
from ...schemas.invoice import InvoiceDetail, InvoiceListResponse
from ...schemas.invoice_line_item import (
    BatchAdjustmentsResponse,
    BatchAdjustmentsUpdate,
)
from ...services import (
    BatchUpdateError,
    NotFoundError,
    batch_update_adjustments,
    invoice_service,
)

router = APIRouter(tags=["invoices"])


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(session: SessionDep, pagination: PaginationDep):
    return await invoice_service.list_invoices(session, pagination=pagination)


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetail)
async def get_invoice(invoice_id: int, session: SessionDep):
    try:
        return await invoice_service.get_invoice_detail(session, invoice_id=invoice_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch(
    "/invoices/{invoice_id}/adjustments", response_model=BatchAdjustmentsResponse
)
async def patch_invoice_adjustments(
    invoice_id: int,
    payload: BatchAdjustmentsUpdate,
    session: SessionDep,
):
    """Batch update adjustments for multiple line items in an invoice."""
    try:
        updates = [
            (item.invoice_line_item_id, item.adjustments) for item in payload.updates
        ]
        return await batch_update_adjustments(
            session,
            invoice_id=invoice_id,
            updates=updates,
        )
    except BatchUpdateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
