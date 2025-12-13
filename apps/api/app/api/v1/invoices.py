from fastapi import APIRouter, HTTPException

from ...api.deps import PaginationDep, SessionDep
from ...schemas.invoice import InvoiceDetail, InvoiceListResponse
from ...services import NotFoundError, invoice_service

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
