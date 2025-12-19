"""API integration tests for campaign endpoints."""

from __future__ import annotations

from decimal import Decimal


class TestListCampaigns:
    """Tests for GET /api/v1/campaigns."""

    async def test_list_campaigns_empty(self, client):
        """Should return empty list when no campaigns exist."""
        response = await client.get("/api/v1/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert data["campaigns"] == []
        assert data["total"] == 0

    async def test_list_campaigns_with_data(
        self, client, make_campaign, make_line_item
    ):
        """Should return campaigns with correct totals."""
        campaign = await make_campaign(name="Test Campaign")
        await make_line_item(campaign, name="Item 1", booked_amount=Decimal("100.00"))

        response = await client.get("/api/v1/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["campaigns"]) == 1
        assert data["campaigns"][0]["name"] == "Test Campaign"
        assert data["campaigns"][0]["total_booked"] == "100.00"

    async def test_list_campaigns_pagination(self, client, make_campaign):
        """Should respect pagination parameters."""
        for i in range(5):
            await make_campaign(name=f"Campaign {i}")

        response = await client.get("/api/v1/campaigns?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["campaigns"]) == 2

    async def test_list_campaigns_search_case_insensitive(self, client, make_campaign):
        """Should filter by campaign name case-insensitively."""
        await make_campaign(name="Alpha Project")
        await make_campaign(name="Beta Campaign")
        await make_campaign(name="ALPHA TEST")

        response = await client.get("/api/v1/campaigns?search=alpha")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [c["name"] for c in data["campaigns"]]
        assert "Alpha Project" in names
        assert "ALPHA TEST" in names

    async def test_list_campaigns_search_contains_match(self, client, make_campaign):
        """Should match campaign names containing the search term."""
        await make_campaign(name="Test Campaign Alpha")
        await make_campaign(name="Alpha Test")
        await make_campaign(name="Beta Campaign")

        response = await client.get("/api/v1/campaigns?search=Test")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [c["name"] for c in data["campaigns"]]
        assert "Test Campaign Alpha" in names
        assert "Alpha Test" in names

    async def test_list_campaigns_search_escapes_wildcards(self, client, make_campaign):
        """Should escape SQL LIKE wildcards in search term."""
        await make_campaign(name="100% Complete")
        await make_campaign(name="50 Percent Done")
        await make_campaign(name="Test_Underscore")
        await make_campaign(name="Test Normal")

        # Search for literal % character
        response = await client.get(
            "/api/v1/campaigns?search=%25"
        )  # %25 = URL encoded %

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["campaigns"][0]["name"] == "100% Complete"

        # Search for literal _ character
        response = await client.get("/api/v1/campaigns?search=_")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["campaigns"][0]["name"] == "Test_Underscore"

    async def test_list_campaigns_sort_by_name(self, client, make_campaign):
        """Should sort by name."""
        await make_campaign(name="Zebra")
        await make_campaign(name="Apple")
        await make_campaign(name="Mango")

        # Ascending
        response = await client.get("/api/v1/campaigns?sort_by=name&sort_dir=asc")
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["campaigns"]]
        assert names == ["Apple", "Mango", "Zebra"]

        # Descending
        response = await client.get("/api/v1/campaigns?sort_by=name&sort_dir=desc")
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["campaigns"]]
        assert names == ["Zebra", "Mango", "Apple"]

    async def test_list_campaigns_sort_by_total_booked(
        self, client, make_campaign, make_line_item
    ):
        """Should sort by total_booked."""
        c1 = await make_campaign(name="Low")
        c2 = await make_campaign(name="High")
        c3 = await make_campaign(name="Medium")

        await make_line_item(c1, name="Item", booked_amount=Decimal("100.00"))
        await make_line_item(c2, name="Item", booked_amount=Decimal("500.00"))
        await make_line_item(c3, name="Item", booked_amount=Decimal("250.00"))

        # Ascending
        response = await client.get(
            "/api/v1/campaigns?sort_by=total_booked&sort_dir=asc"
        )
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["campaigns"]]
        assert names == ["Low", "Medium", "High"]

        # Descending
        response = await client.get(
            "/api/v1/campaigns?sort_by=total_booked&sort_dir=desc"
        )
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["campaigns"]]
        assert names == ["High", "Medium", "Low"]

    async def test_list_campaigns_sort_by_line_items_count(
        self, client, make_campaign, make_line_item
    ):
        """Should sort by line_items_count."""
        c1 = await make_campaign(name="One")
        c2 = await make_campaign(name="Three")
        c3 = await make_campaign(name="Two")

        await make_line_item(c1, name="Item 1", booked_amount=Decimal("10.00"))
        await make_line_item(c2, name="Item 1", booked_amount=Decimal("10.00"))
        await make_line_item(c2, name="Item 2", booked_amount=Decimal("10.00"))
        await make_line_item(c2, name="Item 3", booked_amount=Decimal("10.00"))
        await make_line_item(c3, name="Item 1", booked_amount=Decimal("10.00"))
        await make_line_item(c3, name="Item 2", booked_amount=Decimal("10.00"))

        # Ascending
        response = await client.get(
            "/api/v1/campaigns?sort_by=line_items_count&sort_dir=asc"
        )
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["campaigns"]]
        assert names == ["One", "Two", "Three"]

    async def test_list_campaigns_search_with_sort(self, client, make_campaign):
        """Should apply both search and sort together."""
        await make_campaign(name="Alpha Test")
        await make_campaign(name="Beta Project")
        await make_campaign(name="Alpha Project")

        response = await client.get(
            "/api/v1/campaigns?search=Alpha&sort_by=name&sort_dir=desc"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [c["name"] for c in data["campaigns"]]
        assert names == ["Alpha Test", "Alpha Project"]

    async def test_list_campaigns_search_with_pagination(self, client, make_campaign):
        """Should apply search with pagination correctly."""
        for i in range(5):
            await make_campaign(name=f"Test Campaign {i}")
        await make_campaign(name="Other Project")

        response = await client.get("/api/v1/campaigns?search=Test&limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Total matching search
        assert len(data["campaigns"]) == 2  # Page size

    async def test_list_campaigns_default_sort(self, client, make_campaign):
        """Should default to sorting by ID ascending."""
        c3 = await make_campaign(name="Third")
        c1 = await make_campaign(name="First")
        c2 = await make_campaign(name="Second")

        response = await client.get("/api/v1/campaigns")

        assert response.status_code == 200
        ids = [c["id"] for c in response.json()["campaigns"]]
        assert ids == [c3.id, c1.id, c2.id]  # Order by ID ascending


class TestGetCampaign:
    """Tests for GET /api/v1/campaigns/{campaign_id}."""

    async def test_get_campaign_success(self, client, make_campaign, make_line_item):
        """Should return campaign detail with line items."""
        campaign = await make_campaign(name="My Campaign")
        await make_line_item(campaign, name="Item 1", booked_amount=Decimal("50.00"))

        response = await client.get(f"/api/v1/campaigns/{campaign.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign.id
        assert data["name"] == "My Campaign"
        assert len(data["line_items"]) == 1
        assert data["line_items"][0]["name"] == "Item 1"

    async def test_get_campaign_not_found(self, client):
        """Should return 404 for non-existent campaign."""
        response = await client.get("/api/v1/campaigns/99999")

        assert response.status_code == 404
        assert "detail" in response.json()
