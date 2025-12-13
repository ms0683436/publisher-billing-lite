from decimal import Decimal

from pydantic import computed_field

from .base import BaseSchema, MoneySerializerMixin


class LineItemBase(MoneySerializerMixin, BaseSchema):
    """Base LineItem fields"""

    id: int
    campaign_id: int
    name: str
    booked_amount: Decimal


class LineItemInCampaign(LineItemBase):
    """LineItem used in Campaign detail"""

    pass


class LineItemInInvoice(LineItemBase):
    """LineItem used in Invoice detail"""

    actual_amount: Decimal
    adjustments: Decimal
    invoice_line_item_id: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def billable_amount(self) -> Decimal:
        return self.actual_amount + self.adjustments
