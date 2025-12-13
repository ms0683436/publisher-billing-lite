from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from .base import BaseSchema, MoneySerializerMixin, TimestampMixin
from .invoice import InvoiceSummary
from .line_item import LineItemInCampaign


class CampaignBase(BaseSchema):
    """Base Campaign fields"""

    id: int
    name: str


class CampaignListItem(MoneySerializerMixin, CampaignBase):
    """GET /api/v1/campaigns list item"""

    total_booked: Decimal
    total_actual: Decimal
    total_billable: Decimal
    line_items_count: int
    invoice_id: int | None


class CampaignDetail(MoneySerializerMixin, CampaignBase, TimestampMixin):
    """GET /api/v1/campaigns/{id} detail"""

    line_items: list[LineItemInCampaign]
    invoice_summary: InvoiceSummary | None = None


class CampaignListResponse(BaseModel):
    """GET /api/v1/campaigns response"""

    campaigns: list[CampaignListItem]
    total: int
    limit: int
    offset: int
