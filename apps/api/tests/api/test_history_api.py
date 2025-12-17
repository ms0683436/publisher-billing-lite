"""API integration tests for change history endpoints."""

from __future__ import annotations

from decimal import Decimal


def assert_decimal_equal(actual: str, expected: str) -> None:
    """Assert two decimal strings are numerically equal."""
    assert Decimal(actual) == Decimal(expected), f"{actual} != {expected}"


def assert_adjustments_equal(entry: dict, old: str, new: str) -> None:
    """Assert change history entry has expected adjustment values."""
    assert_decimal_equal(entry["old_value"]["adjustments"], old)
    assert_decimal_equal(entry["new_value"]["adjustments"], new)


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

    async def test_get_history_after_adjustment_update(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return history entry after adjustment update."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # Update adjustment
        await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "25.00"},
                ]
            },
        )

        # Get history
        response = await client.get(f"/api/v1/history/invoice_line_item/{ili.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["history"]) == 1

        entry = data["history"][0]
        assert entry["entity_type"] == "invoice_line_item"
        assert entry["entity_id"] == ili.id
        assert_adjustments_equal(entry, "0.00", "25.00")
        assert "changed_by_username" in entry
        assert "created_at" in entry

    async def test_get_history_multiple_changes(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should return multiple history entries in reverse chronological order."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # First update
        await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "10.00"},
                ]
            },
        )

        # Second update
        await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "25.00"},
                ]
            },
        )

        # Get history
        response = await client.get(f"/api/v1/history/invoice_line_item/{ili.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["history"]) == 2

        # Most recent first (reverse chronological)
        assert_adjustments_equal(data["history"][0], "10.00", "25.00")
        assert_adjustments_equal(data["history"][1], "0.00", "10.00")

    async def test_get_history_pagination(
        self,
        client,
        make_campaign,
        make_line_item,
        make_invoice,
        make_invoice_line_item,
    ):
        """Should respect pagination parameters."""
        campaign = await make_campaign(name="Test Campaign")
        li = await make_line_item(campaign, name="Item 1")
        invoice = await make_invoice(campaign)
        ili = await make_invoice_line_item(
            invoice, li, actual_amount=Decimal("100.00"), adjustments=Decimal("0.00")
        )

        # Create 5 history entries
        for i in range(1, 6):
            await client.patch(
                f"/api/v1/invoices/{invoice.id}/adjustments",
                json={
                    "updates": [
                        {"invoice_line_item_id": ili.id, "adjustments": f"{i * 10}.00"},
                    ]
                },
            )

        # Get with pagination
        response = await client.get(
            f"/api/v1/history/invoice_line_item/{ili.id}?limit=2&offset=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["history"]) == 2

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
    """Tests for change history recording functionality."""

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

        # Update with same value
        await client.patch(
            f"/api/v1/invoices/{invoice.id}/adjustments",
            json={
                "updates": [
                    {"invoice_line_item_id": ili.id, "adjustments": "10.00"},
                ]
            },
        )

        # Get history
        response = await client.get(f"/api/v1/history/invoice_line_item/{ili.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["history"] == []

    async def test_comment_history_after_edit(
        self,
        client,
        make_campaign,
        make_user,
        auth_headers,
    ):
        """Should record history when comment is edited."""
        campaign = await make_campaign(name="Test Campaign")
        user = await make_user(username="commenter")
        headers = await auth_headers(user)

        # Create comment
        create_response = await client.post(
            "/api/v1/comments",
            json={
                "content": "Original content",
                "campaign_id": campaign.id,
            },
            headers=headers,
        )
        comment_id = create_response.json()["id"]

        # Edit comment
        await client.put(
            f"/api/v1/comments/{comment_id}",
            json={"content": "Updated content"},
            headers=headers,
        )

        # Get history
        response = await client.get(f"/api/v1/history/comment/{comment_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        entry = data["history"][0]
        assert entry["old_value"] == {"content": "Original content"}
        assert entry["new_value"] == {"content": "Updated content"}
        assert entry["changed_by_username"] == "commenter"
