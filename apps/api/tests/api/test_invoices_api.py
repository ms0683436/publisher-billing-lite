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

    async def test_list_invoices_search_case_insensitive(
        self, client, make_campaign, make_invoice
    ):
        """Should filter by campaign name case-insensitively."""
        c1 = await make_campaign(name="Alpha Project")
        c2 = await make_campaign(name="Beta Campaign")
        c3 = await make_campaign(name="ALPHA TEST")
        await make_invoice(c1)
        await make_invoice(c2)
        await make_invoice(c3)

        response = await client.get("/api/v1/invoices?search=alpha")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [i["campaign_name"] for i in data["invoices"]]
        assert "Alpha Project" in names
        assert "ALPHA TEST" in names

    async def test_list_invoices_search_contains_match(
        self, client, make_campaign, make_invoice
    ):
        """Should match campaign names containing the search term."""
        c1 = await make_campaign(name="Test Campaign Alpha")
        c2 = await make_campaign(name="Alpha Test")
        c3 = await make_campaign(name="Beta Campaign")
        await make_invoice(c1)
        await make_invoice(c2)
        await make_invoice(c3)

        response = await client.get("/api/v1/invoices?search=Test")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [i["campaign_name"] for i in data["invoices"]]
        assert "Test Campaign Alpha" in names
        assert "Alpha Test" in names

    async def test_list_invoices_search_escapes_wildcards(
        self, client, make_campaign, make_invoice
    ):
        """Should escape SQL LIKE wildcards in search term."""
        c1 = await make_campaign(name="100% Complete")
        c2 = await make_campaign(name="50 Percent Done")
        c3 = await make_campaign(name="Test_Underscore")
        c4 = await make_campaign(name="Test Normal")
        await make_invoice(c1)
        await make_invoice(c2)
        await make_invoice(c3)
        await make_invoice(c4)

        # Search for literal % character
        response = await client.get(
            "/api/v1/invoices?search=%25"
        )  # %25 = URL encoded %

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["invoices"][0]["campaign_name"] == "100% Complete"

        # Search for literal _ character
        response = await client.get("/api/v1/invoices?search=_")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["invoices"][0]["campaign_name"] == "Test_Underscore"

    async def test_list_invoices_sort_by_campaign_name(
        self, client, make_campaign, make_invoice
    ):
        """Should sort by campaign_name."""
        c1 = await make_campaign(name="Zebra")
        c2 = await make_campaign(name="Apple")
        c3 = await make_campaign(name="Mango")
        await make_invoice(c1)
        await make_invoice(c2)
        await make_invoice(c3)

        # Ascending
        response = await client.get(
            "/api/v1/invoices?sort_by=campaign_name&sort_dir=asc"
        )
        assert response.status_code == 200
        names = [i["campaign_name"] for i in response.json()["invoices"]]
        assert names == ["Apple", "Mango", "Zebra"]

        # Descending
        response = await client.get(
            "/api/v1/invoices?sort_by=campaign_name&sort_dir=desc"
        )
        assert response.status_code == 200
        names = [i["campaign_name"] for i in response.json()["invoices"]]
        assert names == ["Zebra", "Mango", "Apple"]

    async def test_list_invoices_sort_by_total_billable(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should sort by total_billable."""
        c1 = await make_campaign(name="Low")
        c2 = await make_campaign(name="High")
        c3 = await make_campaign(name="Medium")
        li1 = await make_line_item(c1, name="Item")
        li2 = await make_line_item(c2, name="Item")
        li3 = await make_line_item(c3, name="Item")
        inv1 = await make_invoice(c1)
        inv2 = await make_invoice(c2)
        inv3 = await make_invoice(c3)
        await make_invoice_line_item(inv1, li1, actual_amount=Decimal("100.00"))
        await make_invoice_line_item(inv2, li2, actual_amount=Decimal("500.00"))
        await make_invoice_line_item(inv3, li3, actual_amount=Decimal("250.00"))

        # Ascending
        response = await client.get(
            "/api/v1/invoices?sort_by=total_billable&sort_dir=asc"
        )
        assert response.status_code == 200
        names = [i["campaign_name"] for i in response.json()["invoices"]]
        assert names == ["Low", "Medium", "High"]

        # Descending
        response = await client.get(
            "/api/v1/invoices?sort_by=total_billable&sort_dir=desc"
        )
        assert response.status_code == 200
        names = [i["campaign_name"] for i in response.json()["invoices"]]
        assert names == ["High", "Medium", "Low"]

    async def test_list_invoices_sort_by_line_items_count(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should sort by line_items_count."""
        c1 = await make_campaign(name="One")
        c2 = await make_campaign(name="Three")
        c3 = await make_campaign(name="Two")
        li1_1 = await make_line_item(c1, name="Item 1")
        li2_1 = await make_line_item(c2, name="Item 1")
        li2_2 = await make_line_item(c2, name="Item 2")
        li2_3 = await make_line_item(c2, name="Item 3")
        li3_1 = await make_line_item(c3, name="Item 1")
        li3_2 = await make_line_item(c3, name="Item 2")
        inv1 = await make_invoice(c1)
        inv2 = await make_invoice(c2)
        inv3 = await make_invoice(c3)
        await make_invoice_line_item(inv1, li1_1, actual_amount=Decimal("10.00"))
        await make_invoice_line_item(inv2, li2_1, actual_amount=Decimal("10.00"))
        await make_invoice_line_item(inv2, li2_2, actual_amount=Decimal("10.00"))
        await make_invoice_line_item(inv2, li2_3, actual_amount=Decimal("10.00"))
        await make_invoice_line_item(inv3, li3_1, actual_amount=Decimal("10.00"))
        await make_invoice_line_item(inv3, li3_2, actual_amount=Decimal("10.00"))

        # Ascending
        response = await client.get(
            "/api/v1/invoices?sort_by=line_items_count&sort_dir=asc"
        )
        assert response.status_code == 200
        names = [i["campaign_name"] for i in response.json()["invoices"]]
        assert names == ["One", "Two", "Three"]

    async def test_list_invoices_search_with_sort(
        self, client, make_campaign, make_invoice
    ):
        """Should apply both search and sort together."""
        c1 = await make_campaign(name="Alpha Test")
        c2 = await make_campaign(name="Beta Project")
        c3 = await make_campaign(name="Alpha Project")
        await make_invoice(c1)
        await make_invoice(c2)
        await make_invoice(c3)

        response = await client.get(
            "/api/v1/invoices?search=Alpha&sort_by=campaign_name&sort_dir=desc"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [i["campaign_name"] for i in data["invoices"]]
        assert names == ["Alpha Test", "Alpha Project"]

    async def test_list_invoices_search_with_pagination(
        self, client, make_campaign, make_invoice
    ):
        """Should apply search with pagination correctly."""
        for i in range(5):
            c = await make_campaign(name=f"Test Campaign {i}")
            await make_invoice(c)
        other = await make_campaign(name="Other Project")
        await make_invoice(other)

        response = await client.get("/api/v1/invoices?search=Test&limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Total matching search
        assert len(data["invoices"]) == 2  # Page size

    async def test_list_invoices_default_sort(
        self, client, make_campaign, make_invoice
    ):
        """Should default to sorting by ID ascending."""
        c1 = await make_campaign(name="Third")
        c2 = await make_campaign(name="First")
        c3 = await make_campaign(name="Second")
        inv1 = await make_invoice(c1)
        inv2 = await make_invoice(c2)
        inv3 = await make_invoice(c3)

        response = await client.get("/api/v1/invoices")

        assert response.status_code == 200
        ids = [i["id"] for i in response.json()["invoices"]]
        assert ids == [inv1.id, inv2.id, inv3.id]  # Order by ID ascending


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

    async def test_batch_update_infinity_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should reject Infinity values."""
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
                    {"invoice_line_item_id": ili.id, "adjustments": "Infinity"},
                ]
            },
        )

        assert response.status_code in (400, 422)

    async def test_batch_update_negative_infinity_rejected(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should reject -Infinity values."""
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
                    {"invoice_line_item_id": ili.id, "adjustments": "-Infinity"},
                ]
            },
        )

        assert response.status_code in (400, 422)
