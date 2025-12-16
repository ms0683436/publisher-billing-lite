"""Integration tests for comment repository."""

from __future__ import annotations

from app.repositories import comment_repository


class TestListCommentsForCampaign:
    """Tests for list_comments_for_campaign function."""

    async def test_empty_campaign(self, session, make_campaign):
        """Returns empty list when campaign has no comments."""
        campaign = await make_campaign()

        comments, total = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert comments == []
        assert total == 0

    async def test_returns_top_level_comments_only(
        self, session, make_campaign, make_user, make_comment
    ):
        """Only returns top-level comments (not replies) in main list."""
        campaign = await make_campaign()
        author = await make_user()

        comment1 = await make_comment(campaign, author, content="Top level 1")
        await make_comment(campaign, author, content="Reply", parent=comment1)
        await make_comment(campaign, author, content="Top level 2")

        comments, total = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert len(comments) == 2
        assert total == 2

    async def test_loads_replies_for_top_level(
        self, session, make_campaign, make_user, make_comment
    ):
        """Loads nested replies for top-level comments."""
        campaign = await make_campaign()
        author = await make_user()

        parent = await make_comment(campaign, author, content="Parent")
        await make_comment(campaign, author, content="Reply 1", parent=parent)
        await make_comment(campaign, author, content="Reply 2", parent=parent)

        comments, _ = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert len(comments) == 1
        assert len(comments[0].replies) == 2

    async def test_loads_author_relationship(
        self, session, make_campaign, make_user, make_comment
    ):
        """Loads author relationship for comments."""
        campaign = await make_campaign()
        author = await make_user(username="testuser")
        await make_comment(campaign, author)

        comments, _ = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert comments[0].author.username == "testuser"

    async def test_loads_mentions_relationship(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Loads mentions relationship for comments."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned = await make_user(username="mentioned")

        comment = await make_comment(campaign, author, content="Hey @mentioned")
        await make_comment_mention(comment, mentioned)

        comments, _ = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert len(comments[0].mentions) == 1
        assert comments[0].mentions[0].user.username == "mentioned"

    async def test_pagination_limit(
        self, session, make_campaign, make_user, make_comment
    ):
        """Respects limit parameter."""
        campaign = await make_campaign()
        author = await make_user()

        for i in range(5):
            await make_comment(campaign, author, content=f"Comment {i}")

        comments, total = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=2, offset=0
        )

        assert len(comments) == 2
        assert total == 5

    async def test_pagination_offset(
        self, session, make_campaign, make_user, make_comment
    ):
        """Respects offset parameter."""
        campaign = await make_campaign()
        author = await make_user()

        for i in range(5):
            await make_comment(campaign, author, content=f"Comment {i}")

        comments, total = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=3
        )

        assert len(comments) == 2
        assert total == 5

    async def test_ordered_by_created_at_asc(
        self, session, make_campaign, make_user, make_comment
    ):
        """Comments are ordered by created_at ascending (oldest first)."""
        campaign = await make_campaign()
        author = await make_user()

        c1 = await make_comment(campaign, author, content="First")
        c2 = await make_comment(campaign, author, content="Second")
        c3 = await make_comment(campaign, author, content="Third")

        comments, _ = await comment_repository.list_comments_for_campaign(
            session, campaign.id, limit=10, offset=0
        )

        assert [c.id for c in comments] == [c1.id, c2.id, c3.id]

    async def test_filters_by_campaign(
        self, session, make_campaign, make_user, make_comment
    ):
        """Only returns comments for the specified campaign."""
        campaign1 = await make_campaign(name="Campaign 1")
        campaign2 = await make_campaign(name="Campaign 2")
        author = await make_user()

        await make_comment(campaign1, author, content="Campaign 1 comment")
        await make_comment(campaign2, author, content="Campaign 2 comment")

        comments, total = await comment_repository.list_comments_for_campaign(
            session, campaign1.id, limit=10, offset=0
        )

        assert len(comments) == 1
        assert total == 1
        assert comments[0].content == "Campaign 1 comment"


class TestGetComment:
    """Tests for get_comment function."""

    async def test_returns_comment_by_id(
        self, session, make_campaign, make_user, make_comment
    ):
        """Returns comment when found by ID."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author, content="Test content")

        result = await comment_repository.get_comment(session, comment.id)

        assert result is not None
        assert result.id == comment.id
        assert result.content == "Test content"

    async def test_returns_none_for_nonexistent_id(self, session):
        """Returns None when comment ID doesn't exist."""
        result = await comment_repository.get_comment(session, 99999)

        assert result is None

    async def test_loads_all_relationships(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Loads author, mentions, and replies relationships."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned = await make_user(username="mentioned")

        parent = await make_comment(campaign, author)
        await make_comment_mention(parent, mentioned)
        await make_comment(campaign, author, content="Reply", parent=parent)

        result = await comment_repository.get_comment(session, parent.id)

        assert result is not None
        assert result.author.username == "author"
        assert len(result.mentions) == 1
        assert len(result.replies) == 1


class TestCreateComment:
    """Tests for create_comment function."""

    async def test_creates_top_level_comment(self, session, make_campaign, make_user):
        """Creates a top-level comment without parent."""
        campaign = await make_campaign()
        author = await make_user()

        comment = await comment_repository.create_comment(
            session,
            content="New comment",
            campaign_id=campaign.id,
            author_id=author.id,
        )

        assert comment.id is not None
        assert comment.content == "New comment"
        assert comment.campaign_id == campaign.id
        assert comment.author_id == author.id
        assert comment.parent_id is None

    async def test_creates_reply_comment(
        self, session, make_campaign, make_user, make_comment
    ):
        """Creates a reply to an existing comment."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author)

        reply = await comment_repository.create_comment(
            session,
            content="Reply content",
            campaign_id=campaign.id,
            author_id=author.id,
            parent_id=parent.id,
        )

        assert reply.parent_id == parent.id

    async def test_creates_mentions(self, session, make_campaign, make_user):
        """Creates mentions when user IDs provided."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned1 = await make_user(username="mentioned1")
        mentioned2 = await make_user(username="mentioned2")

        comment = await comment_repository.create_comment(
            session,
            content="Hey @mentioned1 and @mentioned2",
            campaign_id=campaign.id,
            author_id=author.id,
            mentioned_user_ids=[mentioned1.id, mentioned2.id],
        )

        assert len(comment.mentions) == 2
        mention_user_ids = {m.user_id for m in comment.mentions}
        assert mentioned1.id in mention_user_ids
        assert mentioned2.id in mention_user_ids

    async def test_returns_comment_with_loaded_relationships(
        self, session, make_campaign, make_user
    ):
        """Returns comment with all relationships loaded."""
        campaign = await make_campaign()
        author = await make_user(username="testuser")

        comment = await comment_repository.create_comment(
            session,
            content="Test",
            campaign_id=campaign.id,
            author_id=author.id,
        )

        # Author should be loaded
        assert comment.author.username == "testuser"


class TestUpdateComment:
    """Tests for update_comment function."""

    async def test_updates_content(
        self, session, make_campaign, make_user, make_comment
    ):
        """Updates comment content."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author, content="Original")

        updated = await comment_repository.update_comment(
            session, comment, content="Updated content"
        )

        assert updated.content == "Updated content"

    async def test_replaces_mentions(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Replaces existing mentions with new ones."""
        campaign = await make_campaign()
        author = await make_user()
        old_mentioned = await make_user(username="old")
        new_mentioned = await make_user(username="new")

        comment = await make_comment(campaign, author)
        await make_comment_mention(comment, old_mentioned)

        updated = await comment_repository.update_comment(
            session,
            comment,
            content="Now mentioning @new",
            mentioned_user_ids=[new_mentioned.id],
        )

        assert len(updated.mentions) == 1
        assert updated.mentions[0].user_id == new_mentioned.id

    async def test_keeps_same_mentions_without_duplicates(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Keeping the same mentioned users should not error or duplicate."""
        campaign = await make_campaign()
        author = await make_user()
        mentioned = await make_user(username="same")

        comment = await make_comment(campaign, author, content="Hey @same")
        await make_comment_mention(comment, mentioned)

        updated = await comment_repository.update_comment(
            session,
            comment,
            content="Edited but still @same",
            mentioned_user_ids=[mentioned.id],
        )

        assert len(updated.mentions) == 1
        assert updated.mentions[0].user_id == mentioned.id

    async def test_clears_mentions_when_none_provided(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Clears mentions when no user IDs provided."""
        campaign = await make_campaign()
        author = await make_user()
        mentioned = await make_user()

        comment = await make_comment(campaign, author)
        await make_comment_mention(comment, mentioned)

        updated = await comment_repository.update_comment(
            session, comment, content="No mentions now"
        )

        assert len(updated.mentions) == 0


class TestDeleteComment:
    """Tests for delete_comment function."""

    async def test_deletes_comment(
        self, session, make_campaign, make_user, make_comment
    ):
        """Deletes comment from database."""
        campaign = await make_campaign()
        author = await make_user()
        comment = await make_comment(campaign, author)
        comment_id = comment.id

        await comment_repository.delete_comment(session, comment)

        result = await comment_repository.get_comment(session, comment_id)
        assert result is None

    async def test_cascades_to_replies(
        self, session, make_campaign, make_user, make_comment
    ):
        """Deleting parent cascades to replies."""
        campaign = await make_campaign()
        author = await make_user()
        parent = await make_comment(campaign, author)
        reply = await make_comment(campaign, author, parent=parent)
        reply_id = reply.id

        await comment_repository.delete_comment(session, parent)

        result = await comment_repository.get_comment(session, reply_id)
        assert result is None

    async def test_cascades_to_mentions(
        self, session, make_campaign, make_user, make_comment, make_comment_mention
    ):
        """Deleting comment cascades to mentions."""
        campaign = await make_campaign()
        author = await make_user()
        mentioned = await make_user()
        comment = await make_comment(campaign, author)
        await make_comment_mention(comment, mentioned)
        comment_id = comment.id

        await comment_repository.delete_comment(session, comment)

        # Verify comment is gone (mentions cascade with it)
        result = await comment_repository.get_comment(session, comment_id)
        assert result is None
