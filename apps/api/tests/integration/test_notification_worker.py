"""Integration tests for notification worker task processing."""

from __future__ import annotations

from app.repositories import notification_repository
from app.services import notification_service
from app.services.notification_queue import NotificationTask, TaskType


class TestWorkerMentionTaskProcessing:
    """Tests for worker mention task processing logic.

    Note: These tests verify the notification creation logic that the worker uses,
    not the actual Redis queue/dequeue which requires a running Redis instance.
    """

    async def test_mention_creates_notifications(
        self, session, make_user, make_campaign, make_comment
    ):
        """Processing a mention task creates notifications for mentioned users."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        mentioned1 = await make_user(username="alice")
        mentioned2 = await make_user(username="bob")
        comment = await make_comment(campaign, author, content="Hey @alice @bob")

        # Simulate what the worker does
        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[mentioned1, mentioned2],
            author=author,
            comment=comment,
        )
        await session.commit()

        assert len(notifications) == 2

        # Verify notifications were persisted
        for user in [mentioned1, mentioned2]:
            notifs, total = await notification_repository.list_notifications_for_user(
                session, user.id
            )
            assert total == 1
            assert notifs[0].type == "mention"
            assert notifs[0].actor_id == author.id

    async def test_mention_excludes_self_mentions(
        self, session, make_user, make_campaign, make_comment
    ):
        """Self-mentions don't create notifications."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        comment = await make_comment(campaign, author, content="I'm @author")

        notifications = await notification_service.create_mention_notifications(
            session,
            mentioned_users=[author],
            author=author,
            comment=comment,
        )
        await session.commit()

        assert notifications == []

        # No notification for author
        notifs, total = await notification_repository.list_notifications_for_user(
            session, author.id
        )
        assert total == 0


class TestWorkerReplyTaskProcessing:
    """Tests for worker reply task processing logic."""

    async def test_reply_creates_notification(
        self, session, make_user, make_campaign, make_comment
    ):
        """Processing a reply task creates notification for parent author."""
        campaign = await make_campaign()
        parent_author = await make_user(username="parent_author")
        replier = await make_user(username="replier")
        parent_comment = await make_comment(campaign, parent_author)
        reply = await make_comment(campaign, replier, parent=parent_comment)

        # Simulate what the worker does
        notification = await notification_service.create_reply_notification(
            session,
            parent_comment=parent_comment,
            reply_author=replier,
            reply_comment=reply,
        )
        await session.commit()

        assert notification is not None

        # Verify notification was persisted
        notifs, total = await notification_repository.list_notifications_for_user(
            session, parent_author.id
        )
        assert total == 1
        assert notifs[0].type == "reply"
        assert notifs[0].actor_id == replier.id

    async def test_reply_to_self_no_notification(
        self, session, make_user, make_campaign, make_comment
    ):
        """Self-replies don't create notifications."""
        campaign = await make_campaign()
        author = await make_user(username="author")
        parent_comment = await make_comment(campaign, author)
        reply = await make_comment(campaign, author, parent=parent_comment)

        notification = await notification_service.create_reply_notification(
            session,
            parent_comment=parent_comment,
            reply_author=author,
            reply_comment=reply,
        )

        assert notification is None


class TestNotificationTaskSerialization:
    """Tests for NotificationTask JSON serialization."""

    def test_mention_task_serialization(self):
        """Mention task serializes and deserializes correctly."""
        task = NotificationTask(
            task_type=TaskType.MENTION,
            mentioned_user_ids=[1, 2, 3],
            author_id=10,
            comment_id=100,
        )

        json_str = task.to_json()
        restored = NotificationTask.from_json(json_str)

        assert restored.task_type == TaskType.MENTION
        assert restored.mentioned_user_ids == [1, 2, 3]
        assert restored.author_id == 10
        assert restored.comment_id == 100

    def test_reply_task_serialization(self):
        """Reply task serializes and deserializes correctly."""
        task = NotificationTask(
            task_type=TaskType.REPLY,
            parent_comment_id=50,
            reply_author_id=20,
            reply_comment_id=200,
        )

        json_str = task.to_json()
        restored = NotificationTask.from_json(json_str)

        assert restored.task_type == TaskType.REPLY
        assert restored.parent_comment_id == 50
        assert restored.reply_author_id == 20
        assert restored.reply_comment_id == 200
