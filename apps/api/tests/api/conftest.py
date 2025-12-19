"""API test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_session
from app.main import app
from app.services.auth_service import create_access_token

if TYPE_CHECKING:
    from app.models import User


@pytest.fixture(autouse=True)
def mock_change_history_queue(request):
    """Mock change history queue to prevent Procrastinate operations in tests.

    Change history is now processed asynchronously via Procrastinate.
    In tests, we mock the enqueue functions to execute synchronously instead
    of actually enqueueing to Procrastinate.

    Tests can use @pytest.mark.sync_change_history to execute change history
    synchronously for testing the recording functionality.
    """
    from typing import Any

    from app.db import get_session_maker
    from app.repositories import change_history_repository

    marker = request.node.get_closest_marker("sync_change_history")

    if marker:
        # For tests that need change history to be recorded synchronously,
        # mock the enqueue functions to directly call the repository
        session_maker = get_session_maker()

        async def mock_enqueue_batch(
            *,
            entity_type: str,
            changes: list[tuple[int, dict[str, Any] | None, dict[str, Any]]],
            changed_by_user_id: int,
        ) -> bool:
            """Directly record change history (bypass queue for testing)."""
            entries = [
                {
                    "entity_type": entity_type,
                    "entity_id": change[0],
                    "old_value": change[1],
                    "new_value": change[2],
                    "changed_by_user_id": changed_by_user_id,
                }
                for change in changes
                if change[1] != change[2]
            ]
            if entries:
                async with session_maker() as session:
                    await change_history_repository.create_history_entries_batch(
                        session, entries
                    )
                    await session.commit()
            return True

        async def mock_enqueue(
            *,
            entity_type: str,
            entity_id: int,
            old_value: dict[str, Any] | None,
            new_value: dict[str, Any],
            changed_by_user_id: int,
        ) -> bool:
            """Directly record change history (bypass queue for testing)."""
            if old_value == new_value:
                return True
            async with session_maker() as session:
                await change_history_repository.create_history_entry(
                    session,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_value=old_value,
                    new_value=new_value,
                    changed_by_user_id=changed_by_user_id,
                )
                await session.commit()
            return True

        with (
            patch(
                "app.services.invoice_line_item_service.enqueue_change_history_batch",
                new=mock_enqueue_batch,
            ),
            patch(
                "app.services.comment_service.enqueue_change_history",
                new=mock_enqueue,
            ),
        ):
            yield
    else:
        # Default: mock to no-op (don't record change history)
        with (
            patch(
                "app.services.invoice_line_item_service.enqueue_change_history_batch",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.services.comment_service.enqueue_change_history",
                new=AsyncMock(return_value=True),
            ),
        ):
            yield


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
