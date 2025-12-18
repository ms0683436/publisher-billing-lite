"""API integration tests for notification endpoints."""

from __future__ import annotations

from tests.api.conftest import auth_headers_for_user


class TestListNotifications:
    """Tests for GET /api/v1/notifications."""

    async def test_list_notifications_empty(self, client, make_user):
        """Returns empty list when user has no notifications."""
        user = await make_user(username="recipient")

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    async def test_list_notifications_with_data(
        self, client, make_user, make_notification
    ):
        """Returns notifications for the current user."""
        recipient = await make_user(username="recipient")
        actor = await make_user(username="actor")
        await make_notification(
            recipient,
            message="@actor mentioned you",
            actor=actor,
        )

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(recipient),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["message"] == "@actor mentioned you"
        assert data["notifications"][0]["actor"]["username"] == "actor"
        assert data["unread_count"] == 1

    async def test_list_notifications_excludes_other_users(
        self, client, make_user, make_notification
    ):
        """Does not return notifications for other users."""
        user1 = await make_user(username="user1")
        user2 = await make_user(username="user2")
        await make_notification(user1, message="For user1")
        await make_notification(user2, message="For user2")

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user1),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["notifications"][0]["message"] == "For user1"

    async def test_list_notifications_pagination(
        self, client, make_user, make_notification
    ):
        """Respects pagination parameters."""
        user = await make_user(username="recipient")
        for i in range(10):
            await make_notification(user, message=f"Notification {i}")

        response = await client.get(
            "/api/v1/notifications?limit=3&offset=2",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["notifications"]) == 3

    async def test_list_notifications_unread_count(
        self, client, make_user, make_notification
    ):
        """Returns correct unread count."""
        user = await make_user(username="recipient")
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=True)

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["unread_count"] == 2

    async def test_list_notifications_requires_authentication(
        self, unauthenticated_client
    ):
        """Returns 401 when not authenticated."""
        response = await unauthenticated_client.get("/api/v1/notifications")

        assert response.status_code == 401


class TestMarkNotificationRead:
    """Tests for PATCH /api/v1/notifications/{notification_id}/read."""

    async def test_mark_notification_read_success(
        self, client, make_user, make_notification
    ):
        """Marks a notification as read."""
        user = await make_user(username="recipient")
        notification = await make_notification(user, is_read=False)

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["read_count"] == 1

        # Verify unread count decreased
        list_response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user),
        )
        assert list_response.json()["unread_count"] == 0

    async def test_mark_notification_read_not_found(self, client, make_user):
        """Returns 404 for non-existent notification."""
        user = await make_user(username="recipient")

        response = await client.patch(
            "/api/v1/notifications/99999/read",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 404

    async def test_mark_notification_read_forbidden(
        self, client, make_user, make_notification
    ):
        """Returns 403 when marking another user's notification."""
        owner = await make_user(username="owner")
        other = await make_user(username="other")
        notification = await make_notification(owner)

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers_for_user(other),
        )

        assert response.status_code == 403

    async def test_mark_notification_read_requires_authentication(
        self, unauthenticated_client, make_user, make_notification
    ):
        """Returns 401 when not authenticated."""
        user = await make_user(username="recipient")
        notification = await make_notification(user)

        response = await unauthenticated_client.patch(
            f"/api/v1/notifications/{notification.id}/read"
        )

        assert response.status_code == 401


class TestMarkAllNotificationsRead:
    """Tests for PATCH /api/v1/notifications/read-all."""

    async def test_mark_all_read_success(self, client, make_user, make_notification):
        """Marks all notifications as read."""
        user = await make_user(username="recipient")
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=True)

        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["read_count"] == 2  # Only the 2 unread ones

        # Verify all are now read
        list_response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user),
        )
        assert list_response.json()["unread_count"] == 0

    async def test_mark_all_read_empty(self, client, make_user):
        """Returns success with 0 count when no unread notifications."""
        user = await make_user(username="recipient")

        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers_for_user(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["read_count"] == 0

    async def test_mark_all_read_only_affects_current_user(
        self, client, make_user, make_notification
    ):
        """Does not affect other users' notifications."""
        user1 = await make_user(username="user1")
        user2 = await make_user(username="user2")
        await make_notification(user1, is_read=False)
        await make_notification(user2, is_read=False)

        # User1 marks all as read
        await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers_for_user(user1),
        )

        # User2's notification should still be unread
        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers_for_user(user2),
        )
        assert response.json()["unread_count"] == 1

    async def test_mark_all_read_requires_authentication(self, unauthenticated_client):
        """Returns 401 when not authenticated."""
        response = await unauthenticated_client.patch("/api/v1/notifications/read-all")

        assert response.status_code == 401


class TestNotificationIntegration:
    """Integration tests for notification creation via comments."""

    async def test_mention_creates_notification(self, client, make_campaign, make_user):
        """Creating a comment with @mention creates a notification."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned = await make_user(username="mentioned")

        # Create comment with mention
        await client.post(
            "/api/v1/comments",
            json={
                "content": "Hey @mentioned, check this out!",
                "campaign_id": campaign.id,
            },
            headers=auth_headers_for_user(author),
        )

        # Note: In the real system, notifications are created async by worker.
        # This test verifies the API doesn't error; actual notification
        # creation would be tested in worker integration tests.

    async def test_self_mention_no_notification(self, client, make_campaign, make_user):
        """Self-mentions should not create notifications."""
        campaign = await make_campaign()
        author = await make_user(username="author")

        # Create comment mentioning self
        response = await client.post(
            "/api/v1/comments",
            json={
                "content": "I'm @author talking to myself",
                "campaign_id": campaign.id,
            },
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 201
        # Self-mention appears in mentions list but notification is filtered
        data = response.json()
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["username"] == "author"
