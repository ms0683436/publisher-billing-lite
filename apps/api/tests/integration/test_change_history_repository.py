"""Integration tests for change history repository."""

from __future__ import annotations

from app.repositories import change_history_repository


class TestCreateHistoryEntry:
    """Tests for create_history_entry function."""

    async def test_creates_entry_with_old_and_new_value(self, session, make_user):
        """Creates entry with both old and new values."""
        user = await make_user()

        entry = await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value={"adjustments": "0.00"},
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )

        assert entry.id is not None
        assert entry.entity_type == "invoice_line_item"
        assert entry.entity_id == 1
        assert entry.old_value == {"adjustments": "0.00"}
        assert entry.new_value == {"adjustments": "10.00"}
        assert entry.changed_by_user_id == user.id
        assert entry.created_at is not None

    async def test_creates_entry_with_null_old_value(self, session, make_user):
        """Creates entry with null old_value (for creation events)."""
        user = await make_user()

        entry = await change_history_repository.create_history_entry(
            session,
            entity_type="comment",
            entity_id=1,
            old_value=None,
            new_value={"content": "New comment"},
            changed_by_user_id=user.id,
        )

        assert entry.old_value is None
        assert entry.new_value == {"content": "New comment"}


class TestCreateHistoryEntriesBatch:
    """Tests for create_history_entries_batch function."""

    async def test_creates_multiple_entries(self, session, make_user):
        """Creates multiple entries in one batch."""
        user = await make_user()

        entries_data = [
            {
                "entity_type": "invoice_line_item",
                "entity_id": 1,
                "old_value": {"adjustments": "0.00"},
                "new_value": {"adjustments": "10.00"},
                "changed_by_user_id": user.id,
            },
            {
                "entity_type": "invoice_line_item",
                "entity_id": 2,
                "old_value": {"adjustments": "5.00"},
                "new_value": {"adjustments": "15.00"},
                "changed_by_user_id": user.id,
            },
        ]

        entries = await change_history_repository.create_history_entries_batch(
            session, entries_data
        )

        assert len(entries) == 2
        assert entries[0].entity_id == 1
        assert entries[1].entity_id == 2

    async def test_empty_batch_returns_empty_list(self, session):
        """Empty batch returns empty list."""
        entries = await change_history_repository.create_history_entries_batch(
            session, []
        )

        assert entries == []


class TestListHistoryForEntity:
    """Tests for list_history_for_entity function."""

    async def test_returns_empty_for_no_history(self, session):
        """Returns empty list when no history exists."""
        entries, total = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 999
        )

        assert entries == []
        assert total == 0

    async def test_returns_entries_for_entity(self, session, make_user):
        """Returns history entries for specific entity."""
        user = await make_user()

        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value={"adjustments": "0.00"},
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )

        entries, total = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 1
        )

        assert len(entries) == 1
        assert total == 1
        assert entries[0].entity_id == 1

    async def test_filters_by_entity_type_and_id(self, session, make_user):
        """Only returns entries matching both entity_type and entity_id."""
        user = await make_user()

        # Different entity_id
        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value=None,
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )
        # Different entity_type
        await change_history_repository.create_history_entry(
            session,
            entity_type="comment",
            entity_id=2,
            old_value=None,
            new_value={"content": "test"},
            changed_by_user_id=user.id,
        )
        # Target entry
        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=2,
            old_value=None,
            new_value={"adjustments": "20.00"},
            changed_by_user_id=user.id,
        )

        entries, total = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 2
        )

        assert len(entries) == 1
        assert total == 1
        assert entries[0].new_value == {"adjustments": "20.00"}

    async def test_orders_by_created_at_desc(self, session, make_user):
        """Returns entries in reverse chronological order."""
        user = await make_user()

        e1 = await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value={"adjustments": "0.00"},
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )
        e2 = await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value={"adjustments": "10.00"},
            new_value={"adjustments": "20.00"},
            changed_by_user_id=user.id,
        )

        entries, _ = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 1
        )

        # Most recent first (e2 created after e1)
        assert entries[0].id == e2.id
        assert entries[1].id == e1.id

    async def test_pagination_limit(self, session, make_user):
        """Respects limit parameter."""
        user = await make_user()

        for i in range(5):
            await change_history_repository.create_history_entry(
                session,
                entity_type="invoice_line_item",
                entity_id=1,
                old_value={"adjustments": f"{i}.00"},
                new_value={"adjustments": f"{i + 1}.00"},
                changed_by_user_id=user.id,
            )

        entries, total = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 1, limit=2
        )

        assert len(entries) == 2
        assert total == 5

    async def test_pagination_offset(self, session, make_user):
        """Respects offset parameter."""
        user = await make_user()

        for i in range(5):
            await change_history_repository.create_history_entry(
                session,
                entity_type="invoice_line_item",
                entity_id=1,
                old_value={"adjustments": f"{i}.00"},
                new_value={"adjustments": f"{i + 1}.00"},
                changed_by_user_id=user.id,
            )

        entries, total = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 1, limit=10, offset=3
        )

        assert len(entries) == 2
        assert total == 5

    async def test_loads_changed_by_relationship(self, session, make_user):
        """Loads changed_by user relationship."""
        user = await make_user(username="editor")

        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value=None,
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )

        entries, _ = await change_history_repository.list_history_for_entity(
            session, "invoice_line_item", 1
        )

        assert entries[0].changed_by.username == "editor"


class TestListHistoryForEntities:
    """Tests for list_history_for_entities function."""

    async def test_returns_history_for_multiple_entities(self, session, make_user):
        """Returns history for multiple entity IDs."""
        user = await make_user()

        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value=None,
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )
        await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=2,
            old_value=None,
            new_value={"adjustments": "20.00"},
            changed_by_user_id=user.id,
        )
        # Different entity type - should not be included
        await change_history_repository.create_history_entry(
            session,
            entity_type="comment",
            entity_id=1,
            old_value=None,
            new_value={"content": "test"},
            changed_by_user_id=user.id,
        )

        entries = await change_history_repository.list_history_for_entities(
            session, "invoice_line_item", [1, 2]
        )

        assert len(entries) == 2

    async def test_orders_by_created_at_desc(self, session, make_user):
        """Returns entries in reverse chronological order."""
        user = await make_user()

        e1 = await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=1,
            old_value=None,
            new_value={"adjustments": "10.00"},
            changed_by_user_id=user.id,
        )
        e2 = await change_history_repository.create_history_entry(
            session,
            entity_type="invoice_line_item",
            entity_id=2,
            old_value=None,
            new_value={"adjustments": "20.00"},
            changed_by_user_id=user.id,
        )

        entries = await change_history_repository.list_history_for_entities(
            session, "invoice_line_item", [1, 2]
        )

        assert entries[0].id == e2.id
        assert entries[1].id == e1.id

    async def test_respects_limit(self, session, make_user):
        """Respects limit parameter."""
        user = await make_user()

        for i in range(5):
            await change_history_repository.create_history_entry(
                session,
                entity_type="invoice_line_item",
                entity_id=i,
                old_value=None,
                new_value={"adjustments": f"{i}.00"},
                changed_by_user_id=user.id,
            )

        entries = await change_history_repository.list_history_for_entities(
            session, "invoice_line_item", [0, 1, 2, 3, 4], limit=3
        )

        assert len(entries) == 3

    async def test_empty_ids_returns_empty(self, session):
        """Empty entity_ids returns empty list."""
        entries = await change_history_repository.list_history_for_entities(
            session, "invoice_line_item", []
        )

        assert entries == []
