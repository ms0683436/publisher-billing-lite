from decimal import Decimal

from pydantic import BaseModel

from .base import BaseSchema, MoneySerializerMixin, TimestampMixin
from .line_item import LineItemInInvoice


class InvoiceBase(BaseSchema):
    """Base Invoice fields"""

    id: int
    campaign_id: int


class InvoiceSummary(MoneySerializerMixin, InvoiceBase):
    """Invoice summary in Campaign detail"""

    total_actual: Decimal
    total_adjustments: Decimal
    total_billable: Decimal
    line_items_count: int


class InvoiceListItem(MoneySerializerMixin, InvoiceBase):
    """GET /api/v1/invoices list item"""

    campaign_name: str
    total_billable: Decimal
    line_items_count: int


class InvoiceDetail(MoneySerializerMixin, InvoiceBase, TimestampMixin):
    """GET /api/v1/invoices/{id} detail"""

    campaign_name: str
    line_items: list[LineItemInInvoice]
    total_actual: Decimal
    total_adjustments: Decimal
    total_billable: Decimal


class InvoiceListResponse(BaseModel):
    """GET /api/v1/invoices response"""

    invoices: list[InvoiceListItem]
    total: int
    limit: int
    offset: int
