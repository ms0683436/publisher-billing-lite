"""API test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.main import app
from app.services.auth_service import create_access_token

if TYPE_CHECKING:
    from app.models import User


def auth_headers_for_user(user: User) -> dict[str, str]:
    """Generate Authorization headers for a given user."""
    token = create_access_token(user.id, user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(make_user):
    """Factory fixture to generate auth headers for users.

    Usage:
        headers = await auth_headers(user)
        response = await client.get("/api/v1/...", headers=headers)
    """

    async def _auth_headers(user: User | None = None) -> dict[str, str]:
        if user is None:
            user = await make_user(username="auth_default_user")
        return auth_headers_for_user(user)

    return _auth_headers


@pytest.fixture
async def client(session, make_user):
    """Provide an async HTTP client with default authentication."""

    async def override_get_session():
        yield session

    # Create a default authenticated user
    default_user = await make_user(username="default_test_user")
    default_headers = auth_headers_for_user(default_user)

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=default_headers
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def unauthenticated_client(session):
    """Provide an async HTTP client without authentication."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
