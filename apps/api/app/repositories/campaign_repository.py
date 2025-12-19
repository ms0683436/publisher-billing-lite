from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Numeric, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from ..models import Campaign, Invoice, InvoiceLineItem, LineItem
from .utils import escape_like_pattern

MONEY = Numeric(precision=30, scale=15, asdecimal=True)


def _coalesce_money(expr):
    return func.coalesce(expr, sa.literal(0).cast(MONEY))


@dataclass(slots=True)
class CampaignListRow:
    id: int
    name: str
    total_booked: Decimal
    total_actual: Decimal
    total_billable: Decimal
    line_items_count: int
    invoice_id: int | None


@dataclass(slots=True)
class InvoiceSummaryRow:
    id: int
    campaign_id: int
    total_actual: Decimal
    total_adjustments: Decimal
    total_billable: Decimal
    line_items_count: int


def _campaign_line_item_agg_subq() -> Subquery:
    return (
        select(
            LineItem.campaign_id.label("campaign_id"),
            func.count(LineItem.id).label("line_items_count"),
            _coalesce_money(func.sum(LineItem.booked_amount)).label("total_booked"),
        )
        .group_by(LineItem.campaign_id)
        .subquery()
    )


def _campaign_invoice_agg_subq() -> Subquery:
    # Aggregate invoice totals by campaign_id via invoices -> invoice_line_items.
    return (
        select(
            Invoice.campaign_id.label("campaign_id"),
            _coalesce_money(func.sum(InvoiceLineItem.actual_amount)).label(
                "total_actual"
            ),
            _coalesce_money(func.sum(InvoiceLineItem.adjustments)).label(
                "total_adjustments"
            ),
            _coalesce_money(
                func.sum(InvoiceLineItem.actual_amount + InvoiceLineItem.adjustments)
            ).label("total_billable"),
            func.count(InvoiceLineItem.id).label("invoice_line_items_count"),
        )
        .join(InvoiceLineItem, InvoiceLineItem.invoice_id == Invoice.id)
        .group_by(Invoice.campaign_id)
        .subquery()
    )


async def list_campaigns_page(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = "asc",
) -> tuple[list[CampaignListRow], int]:
    """List campaigns with totals, with offset/limit pagination.

    Args:
        session: Database session
        limit: Maximum number of results
        offset: Number of results to skip
        search: Optional search term for campaign name (case-insensitive contains)
        sort_by: Field to sort by (id, name, total_booked, total_actual, total_billable, line_items_count)
        sort_dir: Sort direction (asc or desc)

    Returns:
        (rows, total)
    """

    li_agg = _campaign_line_item_agg_subq()
    inv_agg = _campaign_invoice_agg_subq()

    # Build labeled columns for sorting
    total_booked_col = func.coalesce(
        li_agg.c.total_booked, sa.literal(0).cast(MONEY)
    ).label("total_booked")
    total_actual_col = func.coalesce(
        inv_agg.c.total_actual, sa.literal(0).cast(MONEY)
    ).label("total_actual")
    total_billable_col = func.coalesce(
        inv_agg.c.total_billable, sa.literal(0).cast(MONEY)
    ).label("total_billable")
    line_items_count_col = func.coalesce(li_agg.c.line_items_count, 0).label(
        "line_items_count"
    )

    stmt = (
        select(
            Campaign.id,
            Campaign.name,
            total_booked_col,
            total_actual_col,
            total_billable_col,
            line_items_count_col,
            Invoice.id.label("invoice_id"),
        )
        .select_from(Campaign)
        .outerjoin(li_agg, li_agg.c.campaign_id == Campaign.id)
        .outerjoin(Invoice, Invoice.campaign_id == Campaign.id)
        .outerjoin(inv_agg, inv_agg.c.campaign_id == Campaign.id)
    )

    total_stmt = select(func.count()).select_from(Campaign)

    # Apply search filter
    if search:
        search_filter = Campaign.name.ilike(
            f"%{escape_like_pattern(search)}%", escape="\\"
        )
        stmt = stmt.where(search_filter)
        total_stmt = total_stmt.where(search_filter)

    # Build sort column mapping
    sort_columns = {
        "id": Campaign.id,
        "name": Campaign.name,
        "total_booked": total_booked_col,
        "total_actual": total_actual_col,
        "total_billable": total_billable_col,
        "line_items_count": line_items_count_col,
    }

    # Apply sorting (nulls_last for consistent behavior)
    if sort_by and sort_by in sort_columns:
        sort_col = sort_columns[sort_by]
        if sort_dir == "desc":
            stmt = stmt.order_by(sort_col.desc().nulls_last())
        else:
            stmt = stmt.order_by(sort_col.asc().nulls_last())
    else:
        stmt = stmt.order_by(Campaign.id)

    stmt = stmt.limit(limit).offset(offset)

    total = (await session.execute(total_stmt)).scalar_one()

    rows = (await session.execute(stmt)).all()
    result_rows = [
        CampaignListRow(
            id=row.id,
            name=row.name,
            total_booked=row.total_booked,
            total_actual=row.total_actual,
            total_billable=row.total_billable,
            line_items_count=row.line_items_count,
            invoice_id=row.invoice_id,
        )
        for row in rows
    ]

    return result_rows, int(total)


async def get_campaign(session: AsyncSession, campaign_id: int) -> Campaign | None:
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_campaign_line_items(
    session: AsyncSession,
    campaign_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[LineItem]:
    stmt = (
        select(LineItem)
        .where(LineItem.campaign_id == campaign_id)
        .order_by(LineItem.id)
    )
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    return list((await session.execute(stmt)).scalars().all())


async def get_invoice_summary_for_campaign(
    session: AsyncSession, campaign_id: int
) -> InvoiceSummaryRow | None:
    """Return invoice summary (totals) for a campaign.

    Intended for Campaign detail response.
    """

    inv_agg = _campaign_invoice_agg_subq()

    stmt = (
        select(
            Invoice.id,
            Invoice.campaign_id,
            func.coalesce(inv_agg.c.total_actual, sa.literal(0).cast(MONEY)).label(
                "total_actual"
            ),
            func.coalesce(inv_agg.c.total_adjustments, sa.literal(0).cast(MONEY)).label(
                "total_adjustments"
            ),
            func.coalesce(inv_agg.c.total_billable, sa.literal(0).cast(MONEY)).label(
                "total_billable"
            ),
            func.coalesce(inv_agg.c.invoice_line_items_count, 0).label(
                "line_items_count"
            ),
        )
        .select_from(Invoice)
        .outerjoin(inv_agg, inv_agg.c.campaign_id == Invoice.campaign_id)
        .where(Invoice.campaign_id == campaign_id)
        .limit(1)
    )

    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        return None

    return InvoiceSummaryRow(
        id=row.id,
        campaign_id=row.campaign_id,
        total_actual=row.total_actual,
        total_adjustments=row.total_adjustments,
        total_billable=row.total_billable,
        line_items_count=row.line_items_count,
    )
