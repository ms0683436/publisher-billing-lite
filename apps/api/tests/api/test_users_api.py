"""API integration tests for user endpoints."""

from __future__ import annotations


class TestListUsers:
    """Tests for GET /api/v1/users.

    Note: The client fixture creates a default_test_user for authentication,
    so there's always at least 1 user in the database.
    """

    async def test_list_users_empty(self, client):
        """Returns only the default auth user when no other users exist."""
        response = await client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        # The client fixture creates default_test_user for authentication
        assert data["total"] == 1
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "default_test_user"

    async def test_list_users_with_data(self, client, make_user):
        """Returns users with correct data."""
        await make_user(username="alice", email="alice@example.com")
        await make_user(username="bob", email="bob@example.com")

        response = await client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        # +1 for default_test_user from client fixture
        assert data["total"] == 3
        assert len(data["users"]) == 3
        usernames = [u["username"] for u in data["users"]]
        assert "alice" in usernames
        assert "bob" in usernames

    async def test_list_users_excludes_inactive(self, client, make_user):
        """Excludes inactive users from list."""
        await make_user(username="active")
        await make_user(username="inactive", is_active=False)

        response = await client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        # +1 for default_test_user from client fixture
        # total counts all users (3), but users list only shows active (2)
        assert data["total"] == 3
        assert len(data["users"]) == 2
        usernames = [u["username"] for u in data["users"]]
        assert "active" in usernames
        assert "inactive" not in usernames

    async def test_list_users_pagination(self, client, make_user):
        """Respects pagination parameters."""
        for i in range(5):
            await make_user(username=f"user{i}")

        response = await client.get("/api/v1/users?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        # +1 for default_test_user from client fixture
        assert data["total"] == 6
        assert len(data["users"]) == 2


class TestSearchUsers:
    """Tests for GET /api/v1/users/search."""

    async def test_search_requires_query(self, client):
        """Returns 422 when query is missing."""
        response = await client.get("/api/v1/users/search")

        assert response.status_code == 422

    async def test_search_by_prefix(self, client, make_user):
        """Returns users matching username prefix."""
        await make_user(username="alice")
        await make_user(username="albert")
        await make_user(username="bob")

        response = await client.get("/api/v1/users/search?q=al")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        usernames = [u["username"] for u in data["users"]]
        assert "alice" in usernames
        assert "albert" in usernames
        assert "bob" not in usernames

    async def test_search_case_insensitive(self, client, make_user):
        """Search is case-insensitive."""
        await make_user(username="Alice")

        response = await client.get("/api/v1/users/search?q=ALICE")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1

    async def test_search_excludes_inactive(self, client, make_user):
        """Excludes inactive users from search results."""
        await make_user(username="alice", is_active=True)
        await make_user(username="albert", is_active=False)

        response = await client.get("/api/v1/users/search?q=al")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "alice"


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}."""

    async def test_get_user_success(self, client, make_user):
        """Returns user details for valid ID."""
        user = await make_user(username="alice", email="alice@example.com")

        response = await client.get(f"/api/v1/users/{user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["is_active"] is True

    async def test_get_user_not_found(self, client):
        """Returns 404 for non-existent user."""
        response = await client.get("/api/v1/users/99999")

        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_get_inactive_user(self, client, make_user):
        """Returns inactive user (no filter on get)."""
        user = await make_user(username="inactive", is_active=False)

        response = await client.get(f"/api/v1/users/{user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
