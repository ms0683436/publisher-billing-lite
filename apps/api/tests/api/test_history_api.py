"""API integration tests for change history endpoints.

NOTE: Change history is now processed asynchronously via Procrastinate.
Tests that verify change history recording are in integration tests.
These tests verify the API endpoints work correctly.
"""

from __future__ import annotations

from decimal import Decimal


def assert_decimal_equal(actual: str, expected: str) -> None:
    """Assert two decimal strings are numerically equal."""
    assert Decimal(actual) == Decimal(expected), f"{actual} != {expected}"


class TestGetEntityHistory:
    """Tests for GET /api/v1/history/{entity_type}/{entity_id}."""

    async def test_get_history_empty(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return empty list when no history exists."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        response = await client.get(f"/api/v1/history/invoice_line_item/{ili.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []
        assert data["total"] == 0

    async def test_get_history_invalid_entity_type(self, client):
        """Should return 422 for invalid entity type."""
        response = await client.get("/api/v1/history/invalid_type/1")

        assert response.status_code == 422

    async def test_get_history_requires_authentication(
        self,
        unauthenticated_client,
    ):
        """Should return 401 without authentication."""
        response = await unauthenticated_client.get(
            "/api/v1/history/invoice_line_item/1"
        )

        assert response.status_code == 401


class TestChangeHistoryRecording:
    """Tests for change history recording functionality.

    NOTE: Change history is now processed asynchronously via Procrastinate.
    These tests verify that the API still works correctly and doesn't fail
    when change history is processed in the background.
    """

    async def test_no_history_when_value_unchanged(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should not record history when value doesn't change."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("10.00")
        )

        # Update with same value - this should succeed without error
        response = await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "10.00"},
                ]
            },
        )

        assert response.status_code == 200

        # Get history - should be empty since no actual change
        response = await client.get(f"/api/v1/history/invoice_line_item/{ili.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["history"] == []
