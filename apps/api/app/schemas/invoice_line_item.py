from datetime import datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, computed_field, field_validator

from .base import MoneySerializerMixin


class InvoiceLineItemResponse(MoneySerializerMixin, BaseModel):
    """Invoice line item response with computed billable amount."""

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


class AdjustmentItem(BaseModel):
    """Single adjustment in a batch update"""

    invoice_line_item_id: int
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


class BatchAdjustmentsUpdate(BaseModel):
    """PATCH /api/v1/invoices/{id}/adjustments request"""

    updates: list[AdjustmentItem]

    @field_validator("updates")
    @classmethod
    def validate_non_empty(cls, v: list[AdjustmentItem]) -> list[AdjustmentItem]:
        if not v:
            raise ValueError("updates list cannot be empty")
        return v


class BatchAdjustmentsResponse(BaseModel):
    """PATCH /api/v1/invoices/{id}/adjustments response"""

    invoice_id: int
    updated: list[InvoiceLineItemResponse]
