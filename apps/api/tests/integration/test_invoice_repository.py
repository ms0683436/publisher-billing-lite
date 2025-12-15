"""Integration tests for invoice repository."""

from __future__ import annotations

from decimal import Decimal

from app.repositories import invoice_repository


class TestListInvoicesPage:
    """Tests for list_invoices_page function."""

    async def test_empty_database_returns_empty_list(self, session):
        """When no invoices exist, return empty list and zero total."""
        rows, total = await invoice_repository.list_invoices_page(
            session, limit=10, offset=0
        )
        assert rows == []
        assert total == 0

    async def test_single_invoice_no_line_items(
        self, session, make_campaign, make_invoice
    ):
        """Invoice with no line items should have zero totals."""
        campaign = await make_campaign(name="Test Campaign")
        await make_invoice(campaign)

        rows, total = await invoice_repository.list_invoices_page(
            session, limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert rows[0].campaign_name == "Test Campaign"
        assert rows[0].total_billable == Decimal("0")
        assert rows[0].line_items_count == 0

    async def test_invoice_with_line_items_totals(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Invoice totals should sum line item amounts correctly."""
        campaign = await make_campaign(name="Campaign")
        li1 = await make_line_item(campaign, name="Item 1")
        li2 = await make_line_item(campaign, name="Item 2")
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice, li1, actual_amount=Decimal("100.00"), adjustments=Decimal("10.00")
        )
        await make_invoice_line_item(
            invoice, li2, actual_amount=Decimal("50.00"), adjustments=Decimal("-5.00")
        )

        rows, total = await invoice_repository.list_invoices_page(
            session, limit=10, offset=0
        )

        assert total == 1
        # billable = (100+10) + (50-5) = 110 + 45 = 155
        assert rows[0].total_billable == Decimal("155.00")
        assert rows[0].line_items_count == 2

    async def test_pagination_limit(self, session, make_campaign, make_invoice):
        """Limit parameter should restrict returned rows."""
        for i in range(5):
            campaign = await make_campaign(name=f"Campaign {i}")
            await make_invoice(campaign)

        rows, total = await invoice_repository.list_invoices_page(
            session, limit=2, offset=0
        )

        assert total == 5
        assert len(rows) == 2

    async def test_pagination_offset(self, session, make_campaign, make_invoice):
        """Offset parameter should skip rows."""
        for i in range(5):
            campaign = await make_campaign(name=f"Campaign {i}")
            await make_invoice(campaign)

        rows, total = await invoice_repository.list_invoices_page(
            session, limit=10, offset=3
        )

        assert total == 5
        assert len(rows) == 2


class TestGetInvoiceHeader:
    """Tests for get_invoice_header function."""

    async def test_get_nonexistent_invoice(self, session):
        """Should return None for non-existent invoice."""
        result = await invoice_repository.get_invoice_header(session, 99999)
        assert result is None

    async def test_get_invoice_header_with_totals(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return invoice header with calculated totals."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("15.00")
        )

        result = await invoice_repository.get_invoice_header(session, invoice.id)

        assert result is not None
        assert result.id == invoice.id
        assert result.campaign_id == campaign.id
        assert result.campaign_name == "Test Campaign"
        assert result.total_actual == Decimal("100.00")
        assert result.total_adjustments == Decimal("15.00")
        assert result.total_billable == Decimal("115.00")
        assert result.line_items_count == 1
        # Timestamps should be set
        assert result.created_at is not None
        assert result.updated_at is not None


class TestListInvoiceLineItems:
    """Tests for list_invoice_line_items function."""

    async def test_empty_invoice_returns_empty_list(
        self, session, make_campaign, make_invoice
    ):
        """Invoice with no line items should return empty list."""
        campaign = await make_campaign(name="Campaign")
        invoice = await make_invoice(campaign)

        result = await invoice_repository.list_invoice_line_items(session, invoice.id)

        assert result == []

    async def test_list_invoice_line_items_with_details(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return line items with all details."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(
            campaign, name="Test Item", booked_amount=Decimal("100")
        )
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("80.00"), adjustments=Decimal("5.00")
        )

        result = await invoice_repository.list_invoice_line_items(session, invoice.id)

        assert len(result) == 1
        row = result[0]
        assert row.invoice_line_item_id == ili.id
        assert row.id == li.id  # line_item_id
        assert row.campaign_id == campaign.id
        assert row.name == "Test Item"
        assert row.booked_amount == Decimal("100")
        assert row.actual_amount == Decimal("80.00")
        assert row.adjustments == Decimal("5.00")

    async def test_pagination(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should support limit and offset pagination."""
        campaign = await make_campaign(name="Campaign")
        invoice = await make_invoice(campaign)
        for i in range(5):
            li = await make_line_item(campaign, name=f"Item {i}")
            await make_invoice_line_item(invoice, li)

        result = await invoice_repository.list_invoice_line_items(
            session, invoice.id, limit=2, offset=1
        )

        assert len(result) == 2
