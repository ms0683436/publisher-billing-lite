"""API integration tests for authentication endpoints."""

from __future__ import annotations

from tests.api.conftest import auth_headers_for_user


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, unauthenticated_client, make_user):
        """Returns access token and sets refresh cookie on valid credentials."""
        await make_user(username="alice")

        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15 minutes in seconds
        assert "refresh_token" not in data  # Refresh token is in cookie

        # Verify refresh token cookie is set
        cookies = response.cookies
        assert "refresh_token" in cookies

    async def test_login_invalid_username(self, unauthenticated_client, make_user):
        """Returns 401 for non-existent username."""
        await make_user(username="alice")

        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "testpassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_invalid_password(self, unauthenticated_client, make_user):
        """Returns 401 for wrong password."""
        await make_user(username="alice")

        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_inactive_user(self, unauthenticated_client, make_user):
        """Returns 401 for inactive user."""
        await make_user(username="inactive", is_active=False)

        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "inactive", "password": "password123"},
        )

        assert response.status_code == 401

    async def test_login_missing_username(self, unauthenticated_client):
        """Returns 422 when username is missing."""
        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"password": "testpassword"},
        )

        assert response.status_code == 422

    async def test_login_missing_password(self, unauthenticated_client):
        """Returns 422 when password is missing."""
        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice"},
        )

        assert response.status_code == 422

    async def test_login_empty_username(self, unauthenticated_client):
        """Returns 422 for empty username."""
        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "testpassword"},
        )

        assert response.status_code == 422

    async def test_login_empty_password(self, unauthenticated_client):
        """Returns 422 for empty password."""
        response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": ""},
        )

        assert response.status_code == 422


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, unauthenticated_client, make_user):
        """Returns new access token when refresh token is valid."""
        await make_user(username="alice")

        # First login to get refresh token cookie
        login_response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert login_response.status_code == 200

        # Use cookies from login for refresh
        refresh_response = await unauthenticated_client.post(
            "/api/v1/auth/refresh",
            cookies=login_response.cookies,
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    async def test_refresh_without_cookie(self, unauthenticated_client):
        """Returns 401 when no refresh token cookie is provided."""
        response = await unauthenticated_client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "Refresh token not found" in response.json()["detail"]

    async def test_refresh_invalid_token(self, unauthenticated_client):
        """Returns 401 for invalid refresh token."""
        response = await unauthenticated_client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_refresh_with_access_token(self, unauthenticated_client, make_user):
        """Returns 401 when using access token instead of refresh token."""
        from app.services.auth_service import create_access_token

        user = await make_user(username="alice")
        access_token = create_access_token(user.id, user.username)

        response = await unauthenticated_client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": access_token},
        )

        assert response.status_code == 401

    async def test_refresh_inactive_user(self, unauthenticated_client, make_user):
        """Returns 401 when user has been deactivated after token was issued."""
        from app.services.auth_service import create_refresh_token

        user = await make_user(username="alice", is_active=False)
        refresh_token = create_refresh_token(user.id, user.username)

        response = await unauthenticated_client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/v1/auth/logout."""

    async def test_logout_clears_cookie(self, unauthenticated_client, make_user):
        """Logout clears the refresh token cookie."""
        await make_user(username="alice")

        # Login first
        login_response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert login_response.status_code == 200

        # Logout
        logout_response = await unauthenticated_client.post(
            "/api/v1/auth/logout",
            cookies=login_response.cookies,
        )

        assert logout_response.status_code == 200
        data = logout_response.json()
        assert data["message"] == "Logged out successfully"

    async def test_logout_without_cookie(self, unauthenticated_client):
        """Logout succeeds even without refresh token cookie."""
        response = await unauthenticated_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me."""

    async def test_get_me_success(self, client, make_user):
        """Returns current user info when authenticated."""
        user = await make_user(username="testuser", email="test@example.com")

        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    async def test_get_me_unauthenticated(self, unauthenticated_client):
        """Returns 401 when not authenticated."""
        response = await unauthenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_me_invalid_token(self, unauthenticated_client):
        """Returns 401 for invalid token."""
        response = await unauthenticated_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_get_me_expired_token(self, unauthenticated_client, make_user):
        """Returns 401 for expired token."""
        import time

        import jwt

        from app.services.auth_service import TOKEN_TYPE_ACCESS
        from app.settings import get_settings

        user = await make_user(username="alice")
        settings = get_settings()

        # Create expired token
        expired_payload = {
            "sub": str(user.id),
            "username": user.username,
            "type": TOKEN_TYPE_ACCESS,
            "exp": time.time() - 100,
        }
        expired_token = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        response = await unauthenticated_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401


class TestAuthenticationFlow:
    """Integration tests for complete authentication flow."""

    async def test_full_auth_flow(self, unauthenticated_client, make_user):
        """Test complete login -> access protected resource -> refresh -> logout flow."""
        await make_user(username="flowtest", email="flow@example.com")

        # 1. Login
        login_response = await unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username": "flowtest", "password": "password123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        cookies = login_response.cookies

        # 2. Access protected resource with access token
        me_response = await unauthenticated_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowtest"

        # 3. Refresh tokens
        refresh_response = await unauthenticated_client.post(
            "/api/v1/auth/refresh",
            cookies=cookies,
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token  # Should get a valid token

        # 4. Access protected resource with new token
        me_response2 = await unauthenticated_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response2.status_code == 200

        # 5. Logout
        logout_response = await unauthenticated_client.post(
            "/api/v1/auth/logout",
            cookies=refresh_response.cookies,
        )
        assert logout_response.status_code == 200

    async def test_protected_endpoints_require_auth(self, unauthenticated_client):
        """Verify that protected endpoints return 401 without authentication."""
        endpoints = [
            ("GET", "/api/v1/campaigns"),
            ("GET", "/api/v1/invoices"),
            ("GET", "/api/v1/users"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = await unauthenticated_client.get(url)
            assert response.status_code == 401, f"{method} {url} should require auth"
