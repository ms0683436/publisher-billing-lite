"""Unit tests for notification service business logic."""

from __future__ import annotations

import pytest

from app.services import notification_service


class TestCreateMentionNotifications:
    """Tests for create_mention_notifications function."""

    async def test_creates_notifications_for_mentioned_users(
        self, session, make_user, make_campaign, make_comment
    ):
        """Creates notifications for all mentioned users."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned1 = await make_user(username="alice")
        mentioned2 = await make_user(username="bob")
        comment = await make_comment(campaign, author, content="Hey @alice and @bob")

        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[mentioned1, mentioned2],
            author=author,
            comment=comment,
        )
        await session.commit()

        assert len(notifications) == 2
        user_ids = {n.user_id for n in notifications}
        assert mentioned1.id in user_ids
        assert mentioned2.id in user_ids

    async def test_excludes_self_mentions(
        self, session, make_user, make_campaign, make_comment
    ):
        """Does not create notification when author mentions themselves."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        comment = await make_comment(campaign, author, content="I'm @author")

        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[author],  # Author mentioning themselves
            author=author,
            comment=comment,
        )
        await session.commit()

        assert notifications == []

    async def test_creates_correct_message(
        self, session, make_user, make_campaign, make_comment
    ):
        """Creates notification with correct message format."""
        campaign = await make_campaign()
        author = await make_user(username="alice")
        mentioned = await make_user(username="bob")
        comment = await make_comment(campaign, author, content="Hey @bob")

        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[mentioned],
            author=author,
            comment=comment,
        )
        await session.commit()

        assert notifications[0].message == "@alice mentioned you in a comment"
        assert notifications[0].type == "mention"
        assert notifications[0].actor_id == author.id
        assert notifications[0].comment_id == comment.id

    async def test_returns_empty_for_empty_mentions(
        self, session, make_user, make_campaign, make_comment
    ):
        """Returns empty list when no users are mentioned."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        comment = await make_comment(campaign, author, content="No mentions here")

        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[],
            author=author,
            comment=comment,
        )

        assert notifications == []


class TestCreateReplyNotification:
    """Tests for create_reply_notification function."""

    async def test_creates_notification_for_parent_author(
        self, session, make_user, make_campaign, make_comment
    ):
        """Creates notification for parent comment author."""
        campaign = await make_campaign()
        parent_author = await make_user(username="parent_author")
        replier = await make_user(username="replier")
        parent_comment = await make_comment(
            campaign, parent_author, content="Original comment"
        )
        reply = await make_comment(
            campaign, replier, content="Reply", parent=parent_comment
        )

        notification = await notification_service.create_reply_notification(
            session,
            parent_comment=parent_comment,
            reply_author=replier,
            reply_comment=reply,
        )
        await session.commit()

        assert notification is not None
        assert notification.user_id == parent_author.id
        assert notification.message == "@replier replied to your comment"
        assert notification.type == "reply"
        assert notification.actor_id == replier.id
        assert notification.comment_id == reply.id

    async def test_no_notification_for_self_reply(
        self, session, make_user, make_campaign, make_comment
    ):
        """Does not create notification when author replies to own comment."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        parent_comment = await make_comment(campaign, author, content="My comment")
        reply = await make_comment(
            campaign, author, content="My reply", parent=parent_comment
        )

        notification = await notification_service.create_reply_notification(
            session,
            parent_comment=parent_comment,
            reply_author=author,
            reply_comment=reply,
        )

        assert notification is None


class TestListNotifications:
    """Tests for list_notifications function."""

    async def test_returns_notification_list_response(
        self, session, make_user, make_notification
    ):
        """Returns NotificationListResponse with correct structure."""
        user = await make_user(username="user")
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=True)

        response = await notification_service.list_notifications(
            session, user_id=user.id, limit=10, offset=0
        )

        assert response.total == 2
        assert len(response.notifications) == 2
        assert response.unread_count == 1

    async def test_respects_pagination(self, session, make_user, make_notification):
        """Respects limit and offset parameters."""
        user = await make_user(username="user")
        for _ in range(10):
            await make_notification(user)

        response = await notification_service.list_notifications(
            session, user_id=user.id, limit=3, offset=2
        )

        assert response.total == 10
        assert len(response.notifications) == 3


class TestMarkAsRead:
    """Tests for mark_as_read function."""

    async def test_marks_notification_as_read(
        self, session, make_user, make_notification
    ):
        """Marks a notification as read and returns success response."""
        user = await make_user(username="user")
        notification = await make_notification(user, is_read=False)

        response = await notification_service.mark_as_read(
            session,
            notification_id=notification.id,
            current_user_id=user.id,
        )

        assert response.success is True
        assert response.read_count == 1

    async def test_raises_not_found_for_nonexistent(self, session, make_user):
        """Raises NotFoundError for nonexistent notification."""
        user = await make_user(username="user")

        with pytest.raises(notification_service.NotFoundError):
            await notification_service.mark_as_read(
                session,
                notification_id=99999,
                current_user_id=user.id,
            )

    async def test_raises_forbidden_for_other_user(
        self, session, make_user, make_notification
    ):
        """Raises ForbiddenError when marking another user's notification."""
        owner = await make_user(username="owner")
        other = await make_user(username="other")
        notification = await make_notification(owner)

        with pytest.raises(notification_service.ForbiddenError):
            await notification_service.mark_as_read(
                session,
                notification_id=notification.id,
                current_user_id=other.id,
            )


class TestMarkAllAsRead:
    """Tests for mark_all_as_read function."""

    async def test_marks_all_notifications_as_read(
        self, session, make_user, make_notification
    ):
        """Marks all user's unread notifications as read."""
        user = await make_user(username="user")
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=False)
        await make_notification(user, is_read=True)

        response = await notification_service.mark_all_as_read(
            session, current_user_id=user.id
        )

        assert response.success is True
        assert response.read_count == 2

    async def test_returns_zero_when_none_unread(
        self, session, make_user, make_notification
    ):
        """Returns read_count=0 when no unread notifications."""
        user = await make_user(username="user")
        await make_notification(user, is_read=True)

        response = await notification_service.mark_all_as_read(
            session, current_user_id=user.id
        )

        assert response.success is True
        assert response.read_count == 0
