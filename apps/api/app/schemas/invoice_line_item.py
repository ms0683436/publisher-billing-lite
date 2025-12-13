from datetime import datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, computed_field, field_validator

from .base import MoneySerializerMixin


class InvoiceLineItemUpdate(BaseModel):
    """PATCH /api/v1/invoice-line-items/{id} request"""

    adjustments: str

    @field_validator("adjustments")
    @classmethod
    def validate_adjustments(cls, v: str) -> str:
        try:
            Decimal(v)
            return v
        except (ValueError, InvalidOperation):
            raise ValueError(
                f"adjustments must be a valid decimal string, got: {v}"
            ) from None


class InvoiceLineItemResponse(MoneySerializerMixin, BaseModel):
    """PATCH /api/v1/invoice-line-items/{id} response"""

    id: int
    invoice_id: int
    line_item_id: int
    actual_amount: Decimal
    adjustments: Decimal
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def billable_amount(self) -> Decimal:
        return self.actual_amount + self.adjustments
