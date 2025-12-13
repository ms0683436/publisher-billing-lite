from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Numeric, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from ..models import Campaign, Invoice, InvoiceLineItem, LineItem

MONEY = Numeric(precision=30, scale=15, asdecimal=True)


def _coalesce_money(expr):
    return func.coalesce(expr, sa.literal(0).cast(MONEY))


@dataclass(slots=True)
class InvoiceListRow:
    id: int
    campaign_id: int
    campaign_name: str
    total_billable: Decimal
    line_items_count: int


@dataclass(slots=True)
class InvoiceHeaderRow:
    id: int
    campaign_id: int
    campaign_name: str
    created_at: datetime
    updated_at: datetime
    total_actual: Decimal
    total_adjustments: Decimal
    total_billable: Decimal
    line_items_count: int


@dataclass(slots=True)
class InvoiceLineItemRow:
    invoice_line_item_id: int
    id: int  # line_item_id (matches schemas.line_item.LineItemBase)
    campaign_id: int
    name: str
    booked_amount: Decimal
    actual_amount: Decimal
    adjustments: Decimal


def _invoice_agg_subq() -> Subquery:
    return (
        select(
            InvoiceLineItem.invoice_id.label("invoice_id"),
            _coalesce_money(func.sum(InvoiceLineItem.actual_amount)).label(
                "total_actual"
            ),
            _coalesce_money(func.sum(InvoiceLineItem.adjustments)).label(
                "total_adjustments"
            ),
            _coalesce_money(
                func.sum(InvoiceLineItem.actual_amount + InvoiceLineItem.adjustments)
            ).label("total_billable"),
            func.count(InvoiceLineItem.id).label("line_items_count"),
        )
        .group_by(InvoiceLineItem.invoice_id)
        .subquery()
    )


async def list_invoices_page(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> tuple[list[InvoiceListRow], int]:
    """List invoices with totals, with offset/limit pagination.

    Returns:
        (rows, total)
    """

    inv_agg = _invoice_agg_subq()

    stmt = (
        select(
            Invoice.id,
            Invoice.campaign_id,
            Campaign.name.label("campaign_name"),
            func.coalesce(inv_agg.c.total_billable, sa.literal(0).cast(MONEY)).label(
                "total_billable"
            ),
            func.coalesce(inv_agg.c.line_items_count, 0).label("line_items_count"),
        )
        .select_from(Invoice)
        .join(Campaign, Campaign.id == Invoice.campaign_id)
        .outerjoin(inv_agg, inv_agg.c.invoice_id == Invoice.id)
        .order_by(Invoice.id)
        .limit(limit)
        .offset(offset)
    )

    total_stmt = select(func.count()).select_from(Invoice)
    total = (await session.execute(total_stmt)).scalar_one()

    rows = (await session.execute(stmt)).all()
    result_rows = [
        InvoiceListRow(
            id=row.id,
            campaign_id=row.campaign_id,
            campaign_name=row.campaign_name,
            total_billable=row.total_billable,
            line_items_count=row.line_items_count,
        )
        for row in rows
    ]

    return result_rows, int(total)


async def get_invoice_header(
    session: AsyncSession, invoice_id: int
) -> InvoiceHeaderRow | None:
    """Get invoice header (campaign + totals).

    Intended for GET /api/v1/invoices/{id}.
    """

    inv_agg = _invoice_agg_subq()

    stmt = (
        select(
            Invoice.id,
            Invoice.campaign_id,
            Campaign.name.label("campaign_name"),
            Invoice.created_at,
            Invoice.updated_at,
            func.coalesce(inv_agg.c.total_actual, sa.literal(0).cast(MONEY)).label(
                "total_actual"
            ),
            func.coalesce(inv_agg.c.total_adjustments, sa.literal(0).cast(MONEY)).label(
                "total_adjustments"
            ),
            func.coalesce(inv_agg.c.total_billable, sa.literal(0).cast(MONEY)).label(
                "total_billable"
            ),
            func.coalesce(inv_agg.c.line_items_count, 0).label("line_items_count"),
        )
        .select_from(Invoice)
        .join(Campaign, Campaign.id == Invoice.campaign_id)
        .outerjoin(inv_agg, inv_agg.c.invoice_id == Invoice.id)
        .where(Invoice.id == invoice_id)
        .limit(1)
    )

    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        return None

    return InvoiceHeaderRow(
        id=row.id,
        campaign_id=row.campaign_id,
        campaign_name=row.campaign_name,
        created_at=row.created_at,
        updated_at=row.updated_at,
        total_actual=row.total_actual,
        total_adjustments=row.total_adjustments,
        total_billable=row.total_billable,
        line_items_count=row.line_items_count,
    )


async def list_invoice_line_items(
    session: AsyncSession,
    invoice_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[InvoiceLineItemRow]:
    """List invoice line items with their underlying line item fields."""

    stmt = (
        select(
            InvoiceLineItem.id.label("invoice_line_item_id"),
            LineItem.id.label("id"),
            LineItem.campaign_id,
            LineItem.name,
            LineItem.booked_amount,
            InvoiceLineItem.actual_amount,
            InvoiceLineItem.adjustments,
        )
        .select_from(InvoiceLineItem)
        .join(LineItem, LineItem.id == InvoiceLineItem.line_item_id)
        .where(InvoiceLineItem.invoice_id == invoice_id)
        .order_by(InvoiceLineItem.id)
    )
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)

    rows = (await session.execute(stmt)).all()
    return [
        InvoiceLineItemRow(
            invoice_line_item_id=row.invoice_line_item_id,
            id=row.id,
            campaign_id=row.campaign_id,
            name=row.name,
            booked_amount=row.booked_amount,
            actual_amount=row.actual_amount,
            adjustments=row.adjustments,
        )
        for row in rows
    ]
