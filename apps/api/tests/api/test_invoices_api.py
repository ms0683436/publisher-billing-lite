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


class TestPatchInvoiceAdjustments:
    """Tests for PATCH /api/v1/invoices/{invoice_id}/adjustments."""

    async def test_batch_update_success(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should update multiple adjustments in one request."""
        campaign = await make_campaign(name="Test Campaign")
        li1 = await make_line_item(campaign, name="Item 1")
        li2 = await make_line_item(campaign, name="Item 2")
        invoice = await make_invoice(campaign)
        ili1 = await make_invoice_line_item(
            invoice, li1, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )
        ili2 = await make_invoice_line_item(
            invoice, li2, actual_amount=Decimal("200.00"), adjustments=Decimal("0.00")
        )

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili1.id, "adjustments": "10.00"},
                    {"invoice_line_item_id": ili2.id, "adjustments": "-5.50"},
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["invoice_id"] == invoice.id
        assert len(data["updated"]) == 2

        # Check updated values
        updated_map = {u["id"]: u for u in data["updated"]}
        assert updated_map[ili1.id]["adjustments"] == "10.00"
        assert updated_map[ili1.id]["billable_amount"] == "110.00"
        assert updated_map[ili2.id]["adjustments"] == "-5.50"
        assert updated_map[ili2.id]["billable_amount"] == "194.50"

    async def test_batch_update_single_item(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should work with single item update."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "25.00"},
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["updated"]) == 1
        assert data["updated"][0]["adjustments"] == "25.00"

    async def test_batch_update_rounding(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should round to 2 decimal places with HALF_UP."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "10.125"},
                ]
            },
        )

        assert response.status_code == 200
        # 10.125 rounds to 10.13 with HALF_UP
        assert response.json()["updated"][0]["adjustments"] == "10.13"

    async def test_batch_update_empty_list_rejected(
        self, client, make_campaign, make_invoice
    ):
        """Should reject empty updates list."""
        campaign = await make_campaign(name="Test Campaign")
        invoice = await make_invoice(campaign)

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={"updates": []},
        )

        assert response.status_code == 422

    async def test_batch_update_invalid_decimal_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should reject invalid decimal values."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "not-a-number"},
                ]
            },
        )

        assert response.status_code == 422

    async def test_batch_update_wrong_invoice_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should reject if invoice_line_item_id belongs to different invoice."""
        campaign1 = await make_campaign(name="Campaign 1")
        campaign2 = await make_campaign(name="Campaign 2")
        li1 = await make_line_item(campaign1, name="Item 1")
        li2 = await make_line_item(campaign2, name="Item 2")
        invoice1 = await make_invoice(campaign1)
        invoice2 = await make_invoice(campaign2)
        ili1 = await make_invoice_line_item(
            invoice1, li1, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )
        await make_invoice_line_item(
            invoice2, li2, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # Try to update ili1 using invoice2's endpoint
        response = await client.patch(
            f"/api/v1/invoices/{invoice2.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili1.id, "adjustments": "10.00"},
                ]
            },
        )

        assert response.status_code == 400
        assert "do not belong to invoice" in response.json()["detail"]

    async def test_batch_update_nonexistent_line_item_rejected(
        self,
        client,
        make_campaign,
        make_invoice,
    ):
        """Should reject if invoice_line_item_id doesn't exist."""
        campaign = await make_campaign(name="Test Campaign")
        invoice = await make_invoice(campaign)

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": 99999, "adjustments": "10.00"},
                ]
            },
        )

        assert response.status_code == 400

    async def test_batch_update_nan_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should reject NaN values."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "NaN"},
                ]
            },
        )

        assert response.status_code in (400, 422)
