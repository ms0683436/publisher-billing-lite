from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import Pagination
from ..repositories import campaign_repository
from ..schemas.campaign import CampaignDetail, CampaignListItem, CampaignListResponse
from ..schemas.invoice import InvoiceSummary
from ..schemas.line_item import LineItemInCampaign
from .errors import NotFoundError


async def list_campaigns(
    session: AsyncSession,
    *,
    pagination: Pagination,
) -> CampaignListResponse:
    rows, total = await campaign_repository.list_campaigns_page(
        session, limit=pagination.limit, offset=pagination.offset
    )

    campaigns = [
        CampaignListItem(
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

    return CampaignListResponse(
        campaigns=campaigns,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_campaign_detail(
    session: AsyncSession, *, campaign_id: int
) -> CampaignDetail:
    campaign = await campaign_repository.get_campaign(session, campaign_id)
    if campaign is None:
        raise NotFoundError("campaign", campaign_id)

    line_items = await campaign_repository.list_campaign_line_items(
        session, campaign_id
    )
    invoice_summary_row = await campaign_repository.get_invoice_summary_for_campaign(
        session, campaign_id
    )

    invoice_summary = (
        None
        if invoice_summary_row is None
        else InvoiceSummary(
            id=invoice_summary_row.id,
            campaign_id=invoice_summary_row.campaign_id,
            total_actual=invoice_summary_row.total_actual,
            total_adjustments=invoice_summary_row.total_adjustments,
            total_billable=invoice_summary_row.total_billable,
            line_items_count=invoice_summary_row.line_items_count,
        )
    )

    return CampaignDetail(
        id=campaign.id,
        name=campaign.name,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        line_items=[LineItemInCampaign.model_validate(li) for li in line_items],
        invoice_summary=invoice_summary,
    )
