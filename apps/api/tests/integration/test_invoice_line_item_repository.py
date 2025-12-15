"""Integration tests for invoice line item repository."""

from __future__ import annotations

from decimal import Decimal

from app.repositories import invoice_line_item_repository


class TestBatchUpdateAdjustments:
    """Tests for batch_update_adjustments function."""

    async def test_batch_update_success(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should update multiple adjustments in one call."""
        campaign = await make_campaign(name="Campaign")
        li1 = await make_line_item(campaign, name="Item 1")
        li2 = await make_line_item(campaign, name="Item 2")
        invoice = await make_invoice(campaign)
        ili1 = await make_invoice_line_item(
            invoice, li1, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )
        ili2 = await make_invoice_line_item(
            invoice, li2, actual_amount=Decimal("200.00"), adjustments=Decimal("0.00")
        )

        updates = [
            (ili1.id, Decimal("10.00")),
            (ili2.id, Decimal("-5.50")),
        ]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert len(result) == 2
        result_map = {ili.id: ili for ili in result}
        assert result_map[ili1.id].adjustments == Decimal("10.00")
        assert result_map[ili2.id].adjustments == Decimal("-5.50")

    async def test_batch_update_single_item(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should work with single item update."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        updates = [(ili.id, Decimal("25.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert len(result) == 1
        assert result[0].adjustments == Decimal("25.00")

    async def test_batch_update_empty_list(self, session, make_campaign, make_invoice):
        """Should return empty list for empty updates."""
        campaign = await make_campaign(name="Campaign")
        invoice = await make_invoice(campaign)

        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, []
        )

        assert result == []

    async def test_batch_update_wrong_invoice_returns_empty(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return empty list if line item belongs to different invoice."""
        campaign1 = await make_campaign(name="Campaign 1")
        campaign2 = await make_campaign(name="Campaign 2")
        li1 = await make_line_item(campaign1, name="Item 1")
        invoice1 = await make_invoice(campaign1)
        invoice2 = await make_invoice(campaign2)
        ili1 = await make_invoice_line_item(
            invoice1, li1, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # Try to update ili1 using invoice2's ID
        updates = [(ili1.id, Decimal("10.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice2.id, updates
        )

        assert result == []

    async def test_batch_update_nonexistent_id_returns_empty(
        self,
        session,
        make_campaign,
        make_invoice,
    ):
        """Should return empty list if line item ID doesn't exist."""
        campaign = await make_campaign(name="Campaign")
        invoice = await make_invoice(campaign)

        updates = [(99999, Decimal("10.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert result == []

    async def test_batch_update_partial_invalid_returns_empty(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return empty if any ID is invalid (all-or-nothing)."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # One valid, one invalid
        updates = [
            (ili.id, Decimal("10.00")),
            (99999, Decimal("20.00")),
        ]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert result == []

    async def test_batch_update_with_for_update_flag(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should work with for_update=True (row locking)."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        updates = [(ili.id, Decimal("15.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates, for_update=True
        )

        assert len(result) == 1
        assert result[0].adjustments == Decimal("15.00")

    async def test_batch_update_negative_adjustments(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should allow negative adjustments."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        updates = [(ili.id, Decimal("-25.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert len(result) == 1
        assert result[0].adjustments == Decimal("-25.00")

    async def test_batch_update_preserves_actual_amount(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should not modify actual_amount when updating adjustments."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("123.45"), adjustments=Decimal("0.00")
        )

        updates = [(ili.id, Decimal("10.00"))]
        result = await invoice_line_item_repository.batch_update_adjustments(
            session, invoice.id, updates
        )

        assert len(result) == 1
        assert result[0].actual_amount == Decimal("123.45")
        assert result[0].adjustments == Decimal("10.00")
