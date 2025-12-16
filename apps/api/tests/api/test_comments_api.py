"""API integration tests for comment endpoints."""

from __future__ import annotations

from tests.api.conftest import auth_headers_for_user


class TestListCampaignComments:
    """Tests for GET /api/v1/campaigns/{campaign_id}/comments."""

    async def test_list_comments_empty(self, client, make_campaign):
        """Returns empty list when campaign has no comments."""
        campaign = await make_campaign()

        response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")

        assert response.status_code == 200
        data = response.json()
        assert data["comments"] == []
        assert data["total"] == 0

    async def test_list_comments_with_data(
        self, client, make_campaign, make_user, make_comment
    ):
        """Returns comments with author information."""
        campaign = await make_campaign()
        author = await make_user(username="alice")
        await make_comment(campaign, author, content="Test comment")

        response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["comments"]) == 1
        assert data["comments"][0]["content"] == "Test comment"
        assert data["comments"][0]["author"]["username"] == "alice"

    async def test_list_comments_includes_replies(
        self, client, make_campaign, make_user, make_comment
    ):
        """Returns top-level comments with nested replies."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author, content="Parent")
        await make_comment(campaign, author, content="Reply", parent=parent)

        response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only top-level
        assert len(data["comments"]) == 1
        assert len(data["comments"][0]["replies"]) == 1
        assert data["comments"][0]["replies"][0]["content"] == "Reply"

    async def test_list_comments_includes_mentions(
        self, client, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Returns comments with mention information."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned = await make_user(username="mentioned")
        comment = await make_comment(campaign, author, content="Hey @mentioned")
        await make_comment_mention(comment, mentioned)

        response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")

        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"][0]["mentions"]) == 1
        assert data["comments"][0]["mentions"][0]["username"] == "mentioned"

    async def test_list_comments_pagination(
        self, client, make_campaign, make_user, make_comment
    ):
        """Respects pagination parameters."""
        campaign = await make_campaign()
        author = await make_user()
        for i in range(5):
            await make_comment(campaign, author, content=f"Comment {i}")

        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/comments?limit=2&offset=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["comments"]) == 2

    async def test_list_comments_campaign_not_found(self, client):
        """Returns 404 for non-existent campaign."""
        response = await client.get("/api/v1/campaigns/99999/comments")

        assert response.status_code == 404


class TestCreateComment:
    """Tests for POST /api/v1/comments."""

    async def test_create_comment_success(self, client, make_campaign, make_user):
        """Creates a new top-level comment."""
        campaign = await make_campaign()
        author = await make_user()

        response = await client.post(
            "/api/v1/comments",
            json={"content": "New comment", "campaign_id": campaign.id},
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "New comment"
        assert data["author"]["id"] == author.id
        assert data["parent_id"] is None

    async def test_create_reply(self, client, make_campaign, make_user, make_comment):
        """Creates a reply to an existing comment."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author)

        response = await client.post(
            "/api/v1/comments",
            json={
                "content": "Reply content",
                "campaign_id": campaign.id,
                "parent_id": parent.id,
            },
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent.id

    async def test_create_comment_with_mentions(self, client, make_campaign, make_user):
        """Creates comment and parses @mentions."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        await make_user(username="bob")

        response = await client.post(
            "/api/v1/comments",
            json={
                "content": "Hey @bob, check this out",
                "campaign_id": campaign.id,
            },
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["username"] == "bob"

    async def test_create_comment_requires_authentication(
        self, unauthenticated_client, make_campaign
    ):
        """Returns 401 when not authenticated."""
        campaign = await make_campaign()

        response = await unauthenticated_client.post(
            "/api/v1/comments",
            json={"content": "Test", "campaign_id": campaign.id},
        )

        assert response.status_code == 401

    async def test_create_comment_campaign_not_found(self, client):
        """Returns 404 for non-existent campaign."""
        response = await client.post(
            "/api/v1/comments",
            json={"content": "Test", "campaign_id": 99999},
        )

        assert response.status_code == 404

    async def test_create_reply_to_reply_forbidden(
        self, client, make_campaign, make_user, make_comment
    ):
        """Returns 403 when replying to a reply (max 1 level)."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author)
        reply = await make_comment(campaign, author, parent=parent)

        response = await client.post(
            "/api/v1/comments",
            json={
                "content": "Reply to reply",
                "campaign_id": campaign.id,
                "parent_id": reply.id,
            },
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 403


class TestUpdateComment:
    """Tests for PUT /api/v1/comments/{comment_id}."""

    async def test_update_comment_success(
        self, client, make_campaign, make_user, make_comment
    ):
        """Updates comment content (author only)."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author, content="Original")

        response = await client.put(
            f"/api/v1/comments/{comment.id}",
            json={"content": "Updated content"},
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"

    async def test_update_comment_updates_mentions(
        self, client, make_campaign, make_user, make_comment
    ):
        """Updates mentions when content changes."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        await make_user(username="alice")
        await make_user(username="bob")
        comment = await make_comment(campaign, author, content="Hey @alice")

        # Verify bob can be found via search API
        search_response = await client.get("/api/v1/users/search?q=bob")
        print(f"Search response: {search_response.json()}")
        assert len(search_response.json()["users"]) == 1, "Bob should be findable"

        response = await client.put(
            f"/api/v1/comments/{comment.id}",
            json={"content": "Now mentioning @bob"},
            headers=auth_headers_for_user(author),
        )

        print(f"Update response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["username"] == "bob"

    async def test_update_comment_same_mentions_no_duplicate(
        self, client, make_campaign, make_user, make_comment
    ):
        """Editing content while keeping same @mentions should not 500."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        await make_user(username="alice")
        comment = await make_comment(campaign, author, content="Hey @alice")

        response = await client.put(
            f"/api/v1/comments/{comment.id}",
            json={"content": "Edited text but still @alice"},
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["username"] == "alice"

    async def test_update_comment_not_author(
        self, client, make_campaign, make_user, make_comment
    ):
        """Returns 403 when user is not the author."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        other = await make_user(username="other")
        comment = await make_comment(campaign, author)

        response = await client.put(
            f"/api/v1/comments/{comment.id}",
            json={"content": "Hacked!"},
            headers=auth_headers_for_user(other),
        )

        assert response.status_code == 403

    async def test_update_comment_not_found(self, client):
        """Returns 404 for non-existent comment."""
        response = await client.put(
            "/api/v1/comments/99999",
            json={"content": "Test"},
        )

        assert response.status_code == 404

    async def test_update_comment_requires_authentication(
        self, unauthenticated_client, make_campaign, make_user, make_comment
    ):
        """Returns 401 when not authenticated."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author)

        response = await unauthenticated_client.put(
            f"/api/v1/comments/{comment.id}",
            json={"content": "Test"},
        )

        assert response.status_code == 401


class TestDeleteComment:
    """Tests for DELETE /api/v1/comments/{comment_id}."""

    async def test_delete_comment_success(
        self, client, make_campaign, make_user, make_comment
    ):
        """Deletes comment (author only)."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author)

        response = await client.delete(
            f"/api/v1/comments/{comment.id}",
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")
        assert get_response.json()["total"] == 0

    async def test_delete_comment_cascades_to_replies(
        self, client, make_campaign, make_user, make_comment
    ):
        """Deleting parent also deletes replies."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author)
        await make_comment(campaign, author, parent=parent)

        response = await client.delete(
            f"/api/v1/comments/{parent.id}",
            headers=auth_headers_for_user(author),
        )

        assert response.status_code == 204

        # Verify all comments deleted
        get_response = await client.get(f"/api/v1/campaigns/{campaign.id}/comments")
        assert get_response.json()["total"] == 0

    async def test_delete_comment_not_author(
        self, client, make_campaign, make_user, make_comment
    ):
        """Returns 403 when user is not the author."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        other = await make_user(username="other")
        comment = await make_comment(campaign, author)

        response = await client.delete(
            f"/api/v1/comments/{comment.id}",
            headers=auth_headers_for_user(other),
        )

        assert response.status_code == 403

    async def test_delete_comment_not_found(self, client):
        """Returns 404 for non-existent comment."""
        response = await client.delete("/api/v1/comments/99999")

        assert response.status_code == 404

    async def test_delete_comment_requires_authentication(
        self, unauthenticated_client, make_campaign, make_user, make_comment
    ):
        """Returns 401 when not authenticated."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author)

        response = await unauthenticated_client.delete(f"/api/v1/comments/{comment.id}")

        assert response.status_code == 401
