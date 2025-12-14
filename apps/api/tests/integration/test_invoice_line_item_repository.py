"""Integration tests for invoice line item repository."""

from __future__ import annotations

from decimal import Decimal


from app.repositories import invoice_line_item_repository


class TestGetInvoiceLineItem:
    """Tests for get_invoice_line_item function."""

    async def test_get_nonexistent_returns_none(self, session):
        """Should return None for non-existent invoice line item."""
        result = await invoice_line_item_repository.get_invoice_line_item(
            session, 99999
        )
        assert result is None

    async def test_get_existing_invoice_line_item(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return invoice line item when it exists."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("50.00"), adjustments=Decimal("5.00")
        )

        result = await invoice_line_item_repository.get_invoice_line_item(
            session, ili.id
        )

        assert result is not None
        assert result.id == ili.id
        assert result.actual_amount == Decimal("50.00")
        assert result.adjustments == Decimal("5.00")


class TestUpdateInvoiceLineItemAdjustments:
    """Tests for update_invoice_line_item_adjustments function."""

    async def test_update_nonexistent_returns_none(self, session):
        """Should return None when updating non-existent item."""
        result = (
            await invoice_line_item_repository.update_invoice_line_item_adjustments(
                session, 99999, adjustments=Decimal("10.00")
            )
        )
        assert result is None

    async def test_update_adjustments_success(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should update adjustments successfully."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        result = (
            await invoice_line_item_repository.update_invoice_line_item_adjustments(
                session, ili.id, adjustments=Decimal("25.50")
            )
        )

        assert result is not None
        assert result.id == ili.id
        assert result.adjustments == Decimal("25.50")
        # actual_amount should remain unchanged
        assert result.actual_amount == Decimal("100.00")

    async def test_update_adjustments_negative_value(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should allow negative adjustments."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        result = (
            await invoice_line_item_repository.update_invoice_line_item_adjustments(
                session, ili.id, adjustments=Decimal("-15.00")
            )
        )

        assert result is not None
        assert result.adjustments == Decimal("-15.00")

    async def test_update_with_for_update_flag(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should work with for_update=True (row locking)."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        result = (
            await invoice_line_item_repository.update_invoice_line_item_adjustments(
                session, ili.id, adjustments=Decimal("10.00"), for_update=True
            )
        )

        assert result is not None
        assert result.adjustments == Decimal("10.00")
