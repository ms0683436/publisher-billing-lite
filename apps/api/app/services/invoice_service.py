from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import Pagination
from ..repositories import invoice_repository
from ..schemas.invoice import InvoiceDetail, InvoiceListItem, InvoiceListResponse
from ..schemas.line_item import LineItemInInvoice
from .errors import NotFoundError


async def list_invoices(
    session: AsyncSession,
    *,
    pagination: Pagination,
    search: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> InvoiceListResponse:
    rows, total = await invoice_repository.list_invoices_page(
        session,
        limit=pagination.limit,
        offset=pagination.offset,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    invoices = [
        InvoiceListItem(
            id=row.id,
            campaign_id=row.campaign_id,
            campaign_name=row.campaign_name,
            total_billable=row.total_billable,
            line_items_count=row.line_items_count,
        )
        for row in rows
    ]

    return InvoiceListResponse(
        invoices=invoices,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_invoice_detail(
    session: AsyncSession, *, invoice_id: int
) -> InvoiceDetail:
    header = await invoice_repository.get_invoice_header(session, invoice_id)
    if header is None:
        raise NotFoundError("invoice", invoice_id)

    line_item_rows = await invoice_repository.list_invoice_line_items(
        session, invoice_id
    )
    line_items = [
        LineItemInInvoice(
            id=row.id,
            campaign_id=row.campaign_id,
            name=row.name,
            booked_amount=row.booked_amount,
            actual_amount=row.actual_amount,
            adjustments=row.adjustments,
            invoice_line_item_id=row.invoice_line_item_id,
        )
        for row in line_item_rows
    ]

    return InvoiceDetail(
        id=header.id,
        campaign_id=header.campaign_id,
        campaign_name=header.campaign_name,
        created_at=header.created_at,
        updated_at=header.updated_at,
        line_items=line_items,
        total_actual=header.total_actual,
        total_adjustments=header.total_adjustments,
        total_billable=header.total_billable,
    )
