"""Unit tests for change history service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.change_history_service import (
    EntityType,
    record_change,
    record_changes_batch,
)


class TestRecordChange:
    """Tests for record_change function."""

    @pytest.mark.asyncio
    async def test_record_change_skips_when_no_changes(self):
        """record_change does nothing when old_value equals new_value."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            await record_change(
                mock_session,
                entity_type=EntityType.INVOICE_LINE_ITEM,
                entity_id=1,
                old_value={"adjustment": "100.00"},
                new_value={"adjustment": "100.00"},
                changed_by_user_id=1,
            )

            mock_repo.create_history_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_change_creates_entry_when_changed(self):
        """record_change creates entry when values differ."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            mock_repo.create_history_entry = AsyncMock()

            await record_change(
                mock_session,
                entity_type=EntityType.INVOICE_LINE_ITEM,
                entity_id=42,
                old_value={"adjustment": "100.00"},
                new_value={"adjustment": "150.00"},
                changed_by_user_id=5,
            )

            mock_repo.create_history_entry.assert_called_once_with(
                mock_session,
                entity_type="invoice_line_item",
                entity_id=42,
                old_value={"adjustment": "100.00"},
                new_value={"adjustment": "150.00"},
                changed_by_user_id=5,
            )

    @pytest.mark.asyncio
    async def test_record_change_creates_entry_for_creation(self):
        """record_change creates entry when old_value is None (creation)."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            mock_repo.create_history_entry = AsyncMock()

            await record_change(
                mock_session,
                entity_type=EntityType.COMMENT,
                entity_id=10,
                old_value=None,
                new_value={"content": "New comment"},
                changed_by_user_id=3,
            )

            mock_repo.create_history_entry.assert_called_once_with(
                mock_session,
                entity_type="comment",
                entity_id=10,
                old_value=None,
                new_value={"content": "New comment"},
                changed_by_user_id=3,
            )


class TestRecordChangesBatch:
    """Tests for record_changes_batch function."""

    @pytest.mark.asyncio
    async def test_record_changes_batch_filters_non_changes(self):
        """record_changes_batch filters out entries with no actual changes."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            mock_repo.create_history_entries_batch = AsyncMock()

            changes = [
                (1, {"value": "10"}, {"value": "20"}),  # Changed
                (2, {"value": "30"}, {"value": "30"}),  # No change
                (3, {"value": "40"}, {"value": "50"}),  # Changed
            ]

            await record_changes_batch(
                mock_session,
                entity_type=EntityType.INVOICE_LINE_ITEM,
                changes=changes,
                changed_by_user_id=7,
            )

            mock_repo.create_history_entries_batch.assert_called_once()
            call_args = mock_repo.create_history_entries_batch.call_args
            entries = call_args[0][1]

            assert len(entries) == 2
            assert entries[0]["entity_id"] == 1
            assert entries[1]["entity_id"] == 3

    @pytest.mark.asyncio
    async def test_record_changes_batch_skips_when_all_unchanged(self):
        """record_changes_batch does not call repo when all entries unchanged."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            mock_repo.create_history_entries_batch = AsyncMock()

            changes = [
                (1, {"value": "10"}, {"value": "10"}),
                (2, {"value": "20"}, {"value": "20"}),
            ]

            await record_changes_batch(
                mock_session,
                entity_type=EntityType.INVOICE_LINE_ITEM,
                changes=changes,
                changed_by_user_id=7,
            )

            mock_repo.create_history_entries_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_changes_batch_empty_list(self):
        """record_changes_batch handles empty changes list."""
        mock_session = AsyncMock()

        with patch(
            "app.services.change_history_service.change_history_repository"
        ) as mock_repo:
            mock_repo.create_history_entries_batch = AsyncMock()

            await record_changes_batch(
                mock_session,
                entity_type=EntityType.CAMPAIGN,
                changes=[],
                changed_by_user_id=1,
            )

            mock_repo.create_history_entries_batch.assert_not_called()
