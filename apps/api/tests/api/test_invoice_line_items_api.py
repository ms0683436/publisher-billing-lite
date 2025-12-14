"""API integration tests for invoice line item endpoints."""

from __future__ import annotations

from decimal import Decimal


class TestPatchInvoiceLineItem:
    """Tests for PATCH /api/v1/invoice-line-items/{id}."""

    async def test_update_adjustments_success(
        self,
        client,
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

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": "25.50"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ili.id
        assert data["adjustments"] == "25.50"
        assert data["actual_amount"] == "100.00"
        # billable = 100 + 25.50 = 125.50
        assert data["billable_amount"] == "125.50"

    async def test_update_adjustments_rounding(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should round adjustments to 2 decimal places."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(invoice, li)

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": "10.555"},  # Should round to 10.56
        )

        assert response.status_code == 200
        data = response.json()
        assert data["adjustments"] == "10.56"

    async def test_update_adjustments_negative(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should allow negative adjustments."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(invoice, li, actual_amount=Decimal("100.00"))

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": "-15.00"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["adjustments"] == "-15.00"
        # billable = 100 - 15 = 85
        assert data["billable_amount"] == "85.00"

    async def test_update_adjustments_not_found(self, client):
        """Should return 404 for non-existent invoice line item."""
        response = await client.patch(
            "/api/v1/invoice-line-items/99999",
            json={"adjustments": "10.00"},
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_update_adjustments_invalid_decimal(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return 422 for invalid decimal string."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(invoice, li)

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": "not-a-number"},
        )

        assert response.status_code == 422

    async def test_update_adjustments_empty_string(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return 422 for empty string."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(invoice, li)

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": ""},
        )

        assert response.status_code == 422

    async def test_update_adjustments_nan_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return 422 for NaN value."""
        campaign = await make_campaign(name="Campaign")
        li = await make_line_item(campaign, name="Item")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(invoice, li)

        response = await client.patch(
            f"/api/v1/invoice-line-items/{ili.id}",
            json={"adjustments": "NaN"},
        )

        assert response.status_code == 422
