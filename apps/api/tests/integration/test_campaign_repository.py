"""Integration tests for campaign repository."""

from __future__ import annotations

from decimal import Decimal


from app.repositories import campaign_repository


class TestListCampaignsPage:
    """Tests for list_campaigns_page function."""

    async def test_empty_database_returns_empty_list(self, session):
        """When no campaigns exist, return empty list and zero total."""
        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=10, offset=0
        )
        assert rows == []
        assert total == 0

    async def test_single_campaign_no_line_items(self, session, make_campaign):
        """Campaign with no line items should have zero totals."""
        await make_campaign(name="Empty Campaign")

        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=10, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert rows[0].name == "Empty Campaign"
        assert rows[0].total_booked == Decimal("0")
        assert rows[0].total_actual == Decimal("0")
        assert rows[0].total_billable == Decimal("0")
        assert rows[0].line_items_count == 0
        assert rows[0].invoice_id is None

    async def test_campaign_with_line_items_totals(
        self, session, make_campaign, make_line_item
    ):
        """Campaign totals should sum line item booked amounts."""
        campaign = await make_campaign(name="Campaign A")
        await make_line_item(campaign, name="Item 1", booked_amount=Decimal("100.00"))
        await make_line_item(campaign, name="Item 2", booked_amount=Decimal("50.50"))

        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=10, offset=0
        )

        assert total == 1
        assert rows[0].total_booked == Decimal("150.50")
        assert rows[0].line_items_count == 2

    async def test_campaign_with_invoice_totals(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Campaign should include invoice totals (actual + adjustments)."""
        campaign = await make_campaign(name="Campaign B")
        line_item = await make_line_item(
            campaign, name="Item 1", booked_amount=Decimal("100.00")
        )
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice,
            line_item,
            actual_amount=Decimal("80.00"),
            adjustments=Decimal("5.00"),
        )

        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=10, offset=0
        )

        assert total == 1
        assert rows[0].total_booked == Decimal("100.00")
        assert rows[0].total_actual == Decimal("80.00")
        # billable = actual + adjustments = 80 + 5 = 85
        assert rows[0].total_billable == Decimal("85.00")
        assert rows[0].invoice_id == invoice.id

    async def test_pagination_limit(self, session, make_campaign):
        """Limit parameter should restrict returned rows."""
        for i in range(5):
            await make_campaign(name=f"Campaign {i}")

        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=2, offset=0
        )

        assert total == 5  # Total count is all campaigns
        assert len(rows) == 2  # But only 2 returned

    async def test_pagination_offset(self, session, make_campaign):
        """Offset parameter should skip rows."""
        for i in range(5):
            await make_campaign(name=f"Campaign {i}")

        rows, total = await campaign_repository.list_campaigns_page(
            session, limit=10, offset=3
        )

        assert total == 5
        assert len(rows) == 2  # 5 total - 3 skipped = 2 remaining


class TestGetCampaign:
    """Tests for get_campaign function."""

    async def test_get_existing_campaign(self, session, make_campaign):
        """Should return campaign when it exists."""
        campaign = await make_campaign(name="My Campaign")

        result = await campaign_repository.get_campaign(session, campaign.id)

        assert result is not None
        assert result.id == campaign.id
        assert result.name == "My Campaign"

    async def test_get_nonexistent_campaign(self, session):
        """Should return None for non-existent campaign."""
        result = await campaign_repository.get_campaign(session, 99999)
        assert result is None


class TestGetInvoiceSummaryForCampaign:
    """Tests for get_invoice_summary_for_campaign function."""

    async def test_no_invoice_returns_none(self, session, make_campaign):
        """Campaign without invoice should return None."""
        campaign = await make_campaign(name="No Invoice")

        result = await campaign_repository.get_invoice_summary_for_campaign(
            session, campaign.id
        )

        assert result is None

    async def test_invoice_with_line_items_totals(
        self,
        session,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Invoice summary should calculate correct totals."""
        campaign = await make_campaign(name="Campaign")
        li1 = await make_line_item(
            campaign, name="Item 1", booked_amount=Decimal("100")
        )
        li2 = await make_line_item(
            campaign, name="Item 2", booked_amount=Decimal("200")
        )
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice, li1, actual_amount=Decimal("90.00"), adjustments=Decimal("10.00")
        )
        await make_invoice_line_item(
            invoice, li2, actual_amount=Decimal("180.00"), adjustments=Decimal("-5.00")
        )

        result = await campaign_repository.get_invoice_summary_for_campaign(
            session, campaign.id
        )

        assert result is not None
        assert result.id == invoice.id
        assert result.campaign_id == campaign.id
        assert result.total_actual == Decimal("270.00")  # 90 + 180
        assert result.total_adjustments == Decimal("5.00")  # 10 + (-5)
        # billable = (90 + 10) + (180 + (-5)) = 100 + 175 = 275
        assert result.total_billable == Decimal("275.00")
        assert result.line_items_count == 2
