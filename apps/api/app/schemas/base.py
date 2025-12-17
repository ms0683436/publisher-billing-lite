from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class BaseSchema(BaseModel):
    """Base class for all schemas"""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin providing created_at/updated_at fields"""

    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime_as_utc(self, value: datetime) -> str:
        """Serialize datetime as UTC with explicit timezone for unambiguous parsing"""
        if value.tzinfo is None:
            # Naive datetime from DB assumed to be UTC (PostgreSQL now() in UTC container)
            value = value.replace(tzinfo=UTC)
        else:
            # Convert any timezone-aware datetime to UTC
            value = value.astimezone(UTC)
        return value.isoformat()


class MoneySerializerMixin:
    """Unified Decimal to string serialization logic"""

    _TWO_DP = Decimal("0.01")

    @field_serializer(
        "booked_amount",
        "actual_amount",
        "adjustments",
        "billable_amount",
        "total_booked",
        "total_actual",
        "total_billable",
        "total_adjustments",
        when_used="json",
        check_fields=False,  # Allow subclass usage
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        # Round HALF_UP to 2 decimal places.
        # For computed fields (e.g. actual + adjustments), computation happens first
        # and this serializer applies rounding at JSON render time.
        rounded = value.quantize(self._TWO_DP, rounding=ROUND_HALF_UP)
        return f"{rounded:.2f}"
