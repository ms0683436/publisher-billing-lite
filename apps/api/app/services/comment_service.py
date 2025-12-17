"""Comment service with business logic for CRUD operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import Pagination
from ..repositories import campaign_repository, comment_repository
from ..schemas.comment import CommentCreate, CommentListResponse, CommentResponse
from ..schemas.user import UserBase
from . import change_history_service
from .change_history_service import EntityType
from .errors import ForbiddenError, NotFoundError
from .mention_service import parse_mentions, resolve_mentions

if TYPE_CHECKING:
    from ..models import Comment

logger = logging.getLogger(__name__)


def _comment_to_response(comment: Comment, *, include_replies: bool) -> CommentResponse:
    """Convert Comment model to CommentResponse schema."""
    replies: list[CommentResponse] = []
    replies_count = 0

    if include_replies:
        replies = [
            _comment_to_response(r, include_replies=False) for r in comment.replies
        ]
        replies_count = len(comment.replies)

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        campaign_id=comment.campaign_id,
        author=UserBase.model_validate(comment.author),
        mentions=[UserBase.model_validate(m.user) for m in comment.mentions],
        parent_id=comment.parent_id,
        replies=replies,
        replies_count=replies_count,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


async def list_comments_for_campaign(
    session: AsyncSession,
    *,
    campaign_id: int,
    pagination: Pagination,
) -> CommentListResponse:
    """List comments for a campaign with nested replies.

    Args:
        session: Database session
        campaign_id: Campaign ID
        pagination: Pagination parameters

    Returns:
        CommentListResponse with comments and total count

    Raises:
        NotFoundError: If campaign not found
    """
    # Verify campaign exists
    campaign = await campaign_repository.get_campaign(session, campaign_id)
    if campaign is None:
        raise NotFoundError("campaign", campaign_id)

    comments, total = await comment_repository.list_comments_for_campaign(
        session, campaign_id, limit=pagination.limit, offset=pagination.offset
    )

    return CommentListResponse(
        comments=[_comment_to_response(c, include_replies=True) for c in comments],
        total=total,
    )


async def create_comment(
    session: AsyncSession,
    *,
    data: CommentCreate,
    author_id: int,
) -> CommentResponse:
    """Create a new comment or reply.

    Args:
        session: Database session
        data: Comment creation data
        author_id: ID of the user creating the comment

    Returns:
        Created comment

    Raises:
        NotFoundError: If campaign or parent comment not found
    """
    # Verify campaign exists
    campaign = await campaign_repository.get_campaign(session, data.campaign_id)
    if campaign is None:
        raise NotFoundError("campaign", data.campaign_id)

    # If replying, verify parent comment exists, belongs to same campaign,
    # and is a top-level comment (only 1 level of nesting allowed)
    if data.parent_id is not None:
        parent = await comment_repository.get_comment(session, data.parent_id)
        if parent is None:
            raise NotFoundError("comment", data.parent_id)
        if parent.campaign_id != data.campaign_id:
            raise NotFoundError("comment", data.parent_id)
        if parent.parent_id is not None:
            raise ForbiddenError("reply to", "reply")

    # Parse mentions from content
    usernames = parse_mentions(data.content)
    mentioned_users, unresolved = await resolve_mentions(session, usernames)

    # TODO: Implement notification system for mentioned users
    if mentioned_users:
        logger.info(
            "TODO: Notify users %s about mention in new comment",
            [u.username for u in mentioned_users],
        )

    # Create comment
    comment = await comment_repository.create_comment(
        session,
        content=data.content,
        campaign_id=data.campaign_id,
        author_id=author_id,
        parent_id=data.parent_id,
        mentioned_user_ids=[u.id for u in mentioned_users],
    )

    await session.commit()

    return _comment_to_response(comment, include_replies=True)


async def update_comment(
    session: AsyncSession,
    *,
    comment_id: int,
    content: str,
    current_user_id: int,
) -> CommentResponse:
    """Update a comment (author only).

    Args:
        session: Database session
        comment_id: Comment ID to update
        content: New content
        current_user_id: ID of the user making the request

    Returns:
        Updated comment

    Raises:
        NotFoundError: If comment not found
        ForbiddenError: If user is not the author
    """
    comment = await comment_repository.get_comment(session, comment_id)
    if comment is None:
        raise NotFoundError("comment", comment_id)

    # Check authorization
    if comment.author_id != current_user_id:
        raise ForbiddenError("edit", "comment")

    # Store old content for change history
    old_content = comment.content

    # Parse mentions from new content
    usernames = parse_mentions(content)
    mentioned_users, _ = await resolve_mentions(session, usernames)

    # Update comment
    updated = await comment_repository.update_comment(
        session,
        comment,
        content=content,
        mentioned_user_ids=[u.id for u in mentioned_users],
    )

    # Record change history if content actually changed (use actual stored value)
    if old_content != updated.content:
        await change_history_service.record_change(
            session,
            entity_type=EntityType.COMMENT,
            entity_id=comment_id,
            old_value={"content": old_content},
            new_value={"content": updated.content},
            changed_by_user_id=current_user_id,
        )

    await session.commit()

    return _comment_to_response(updated, include_replies=True)


async def delete_comment(
    session: AsyncSession,
    *,
    comment_id: int,
    current_user_id: int,
) -> None:
    """Delete a comment (author only, cascades to replies).

    Args:
        session: Database session
        comment_id: Comment ID to delete
        current_user_id: ID of the user making the request

    Raises:
        NotFoundError: If comment not found
        ForbiddenError: If user is not the author
    """
    comment = await comment_repository.get_comment(session, comment_id)
    if comment is None:
        raise NotFoundError("comment", comment_id)

    # Check authorization
    if comment.author_id != current_user_id:
        raise ForbiddenError("delete", "comment")

    await comment_repository.delete_comment(session, comment)
    await session.commit()
