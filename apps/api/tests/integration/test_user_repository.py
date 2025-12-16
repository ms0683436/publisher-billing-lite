"""Integration tests for user repository."""

from __future__ import annotations

import pytest

from app.repositories import user_repository


class TestListUsers:
    """Tests for list_users function."""

    async def test_empty_database(self, session):
        """Returns empty list when no users exist."""
        users, total = await user_repository.list_users(session, limit=10, offset=0)

        assert users == []
        assert total == 0

    async def test_returns_active_users_only(self, session, make_user):
        """Only returns active users."""
        await make_user(username="active1")
        await make_user(username="active2")
        await make_user(username="inactive", is_active=False)

        users, total = await user_repository.list_users(session, limit=10, offset=0)

        assert len(users) == 2
        # Total includes inactive users (counts all)
        assert total == 3
        usernames = [u.username for u in users]
        assert "active1" in usernames
        assert "active2" in usernames
        assert "inactive" not in usernames

    async def test_pagination_limit(self, session, make_user):
        """Respects limit parameter."""
        await make_user(username="alice")
        await make_user(username="bob")
        await make_user(username="charlie")

        users, total = await user_repository.list_users(session, limit=2, offset=0)

        assert len(users) == 2
        assert total == 3

    async def test_pagination_offset(self, session, make_user):
        """Respects offset parameter."""
        await make_user(username="alice")
        await make_user(username="bob")
        await make_user(username="charlie")

        users, total = await user_repository.list_users(session, limit=10, offset=2)

        assert len(users) == 1
        assert users[0].username == "charlie"
        assert total == 3

    async def test_ordered_by_username(self, session, make_user):
        """Users are ordered alphabetically by username."""
        await make_user(username="charlie")
        await make_user(username="alice")
        await make_user(username="bob")

        users, _ = await user_repository.list_users(session, limit=10, offset=0)

        usernames = [u.username for u in users]
        assert usernames == ["alice", "bob", "charlie"]


class TestGetUser:
    """Tests for get_user function."""

    async def test_returns_user_by_id(self, session, make_user):
        """Returns user when found by ID."""
        user = await make_user(username="alice")

        result = await user_repository.get_user(session, user.id)

        assert result is not None
        assert result.id == user.id
        assert result.username == "alice"

    async def test_returns_none_for_nonexistent_id(self, session):
        """Returns None when user ID doesn't exist."""
        result = await user_repository.get_user(session, 99999)

        assert result is None

    async def test_returns_inactive_user(self, session, make_user):
        """get_user returns even inactive users (no filter)."""
        user = await make_user(username="inactive", is_active=False)

        result = await user_repository.get_user(session, user.id)

        assert result is not None
        assert result.is_active is False


class TestSearchUsers:
    """Tests for search_users function."""

    async def test_empty_query_returns_all_active(self, session, make_user):
        """Empty query returns all active users up to limit."""
        await make_user(username="alice")
        await make_user(username="bob")
        await make_user(username="inactive", is_active=False)

        results = await user_repository.search_users(session, "", limit=10)

        assert len(results) == 2

    async def test_prefix_match(self, session, make_user):
        """Matches username prefix."""
        await make_user(username="alice")
        await make_user(username="albert")
        await make_user(username="bob")

        results = await user_repository.search_users(session, "al", limit=10)

        assert len(results) == 2
        usernames = [u.username for u in results]
        assert "alice" in usernames
        assert "albert" in usernames
        assert "bob" not in usernames

    async def test_case_insensitive(self, session, make_user):
        """Search is case-insensitive."""
        await make_user(username="Alice")
        await make_user(username="ALBERT")

        results = await user_repository.search_users(session, "AL", limit=10)

        assert len(results) == 2

    async def test_excludes_inactive_users(self, session, make_user):
        """Search excludes inactive users."""
        await make_user(username="alice", is_active=True)
        await make_user(username="albert", is_active=False)

        results = await user_repository.search_users(session, "al", limit=10)

        assert len(results) == 1
        assert results[0].username == "alice"

    async def test_respects_limit(self, session, make_user):
        """Respects limit parameter."""
        await make_user(username="alice")
        await make_user(username="albert")
        await make_user(username="alex")

        results = await user_repository.search_users(session, "al", limit=2)

        assert len(results) == 2

    async def test_ordered_by_username(self, session, make_user):
        """Results are ordered alphabetically."""
        await make_user(username="alex")
        await make_user(username="alice")
        await make_user(username="albert")

        results = await user_repository.search_users(session, "al", limit=10)

        usernames = [u.username for u in results]
        assert usernames == ["albert", "alex", "alice"]


class TestGetUsersByUsernames:
    """Tests for get_users_by_usernames function."""

    async def test_empty_list_returns_empty(self, session):
        """Empty username list returns empty result."""
        results = await user_repository.get_users_by_usernames(session, [])

        assert results == []

    async def test_finds_existing_users(self, session, make_user):
        """Finds users by their usernames."""
        await make_user(username="alice")
        await make_user(username="bob")
        await make_user(username="charlie")

        results = await user_repository.get_users_by_usernames(
            session, ["alice", "bob"]
        )

        assert len(results) == 2
        usernames = [u.username for u in results]
        assert "alice" in usernames
        assert "bob" in usernames

    async def test_case_insensitive(self, session, make_user):
        """Lookup is case-insensitive."""
        await make_user(username="Alice")

        results = await user_repository.get_users_by_usernames(session, ["ALICE"])

        assert len(results) == 1
        assert results[0].username == "Alice"

    async def test_ignores_nonexistent_usernames(self, session, make_user):
        """Nonexistent usernames are silently ignored."""
        await make_user(username="alice")

        results = await user_repository.get_users_by_usernames(
            session, ["alice", "nonexistent"]
        )

        assert len(results) == 1
        assert results[0].username == "alice"

    async def test_excludes_inactive_users(self, session, make_user):
        """Excludes inactive users from results."""
        await make_user(username="alice", is_active=True)
        await make_user(username="bob", is_active=False)

        results = await user_repository.get_users_by_usernames(
            session, ["alice", "bob"]
        )

        assert len(results) == 1
        assert results[0].username == "alice"
