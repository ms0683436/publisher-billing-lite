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
