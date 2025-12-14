"""API integration tests for invoice endpoints."""

from __future__ import annotations

from decimal import Decimal


class TestListInvoices:
    """Tests for GET /api/v1/invoices."""

    async def test_list_invoices_empty(self, client):
        """Should return empty list when no invoices exist."""
        response = await client.get("/api/v1/invoices")

        assert response.status_code == 200
        data = response.json()
        assert data["invoices"] == []
        assert data["total"] == 0

    async def test_list_invoices_with_data(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return invoices with correct totals."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("80.00"), adjustments=Decimal("10.00")
        )

        response = await client.get("/api/v1/invoices")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["invoices"]) == 1
        assert data["invoices"][0]["campaign_name"] == "Test Campaign"
        # billable = 80 + 10 = 90
        assert data["invoices"][0]["total_billable"] == "90.00"

    async def test_list_invoices_pagination(self, client, make_campaign, make_invoice):
        """Should respect pagination parameters."""
        for i in range(5):
            campaign = await make_campaign(name=f"Campaign {i}")
            await make_invoice(campaign)

        response = await client.get("/api/v1/invoices?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["invoices"]) == 2


class TestGetInvoice:
    """Tests for GET /api/v1/invoices/{invoice_id}."""

    async def test_get_invoice_success(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return invoice detail with line items."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1", booked_amount=Decimal("100"))
        invoice = await make_invoice(campaign)
        await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("80.00"), adjustments=Decimal("5.00")
        )

        response = await client.get(f"/api/v1/invoices/{invoice.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice.id
        assert data["campaign_name"] == "Test Campaign"
        assert data["total_actual"] == "80.00"
        assert data["total_adjustments"] == "5.00"
        assert data["total_billable"] == "85.00"
        assert len(data["line_items"]) == 1

    async def test_get_invoice_not_found(self, client):
        """Should return 404 for non-existent invoice."""
        response = await client.get("/api/v1/invoices/99999")

        assert response.status_code == 404
        assert "detail" in response.json()
