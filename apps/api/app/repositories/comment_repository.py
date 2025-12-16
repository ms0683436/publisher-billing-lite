from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Comment, CommentMention


async def list_comments_for_campaign(
    session: AsyncSession,
    campaign_id: int,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Comment], int]:
    """List top-level comments for a campaign with nested replies.

    Args:
        session: Database session
        campaign_id: Campaign ID
        limit: Maximum number of top-level comments
        offset: Number of top-level comments to skip

    Returns:
        Tuple of (comments list with replies, total count)
    """
    # Count total top-level comments
    count_stmt = select(func.count(Comment.id)).where(
        Comment.campaign_id == campaign_id, Comment.parent_id.is_(None)
    )
    total = (await session.execute(count_stmt)).scalar_one()

    # Get top-level comments with author, mentions, and replies (1 level only)
    stmt = (
        select(Comment)
        .where(Comment.campaign_id == campaign_id, Comment.parent_id.is_(None))
        .options(
            selectinload(Comment.author),
            selectinload(Comment.mentions).selectinload(CommentMention.user),
            selectinload(Comment.replies).selectinload(Comment.author),
            selectinload(Comment.replies)
            .selectinload(Comment.mentions)
            .selectinload(CommentMention.user),
        )
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    comments = list((await session.execute(stmt)).scalars().all())

    return comments, total


async def get_comment(
    session: AsyncSession,
    comment_id: int,
) -> Comment | None:
    """Get comment by ID with author, mentions, and replies.

    Args:
        session: Database session
        comment_id: Comment ID

    Returns:
        Comment instance or None
    """
    stmt = (
        select(Comment)
        .where(Comment.id == comment_id)
        .options(
            selectinload(Comment.author),
            selectinload(Comment.mentions).selectinload(CommentMention.user),
            selectinload(Comment.replies).selectinload(Comment.author),
            selectinload(Comment.replies)
            .selectinload(Comment.mentions)
            .selectinload(CommentMention.user),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def create_comment(
    session: AsyncSession,
    *,
    content: str,
    campaign_id: int,
    author_id: int,
    parent_id: int | None = None,
    mentioned_user_ids: list[int] | None = None,
) -> Comment:
    """Create a new comment with mentions.

    Args:
        session: Database session
        content: Comment content
        campaign_id: Campaign ID
        author_id: Author user ID
        parent_id: Parent comment ID (for replies)
        mentioned_user_ids: List of user IDs mentioned in content

    Returns:
        Created comment
    """
    comment = Comment(
        content=content,
        campaign_id=campaign_id,
        author_id=author_id,
        parent_id=parent_id,
    )
    session.add(comment)
    await session.flush()

    # Create mentions
    if mentioned_user_ids:
        for user_id in mentioned_user_ids:
            mention = CommentMention(comment_id=comment.id, user_id=user_id)
            session.add(mention)

    await session.flush()

    # Reload with relationships (comment exists since we just created it)
    result = await get_comment(session, comment.id)
    assert result is not None
    return result


async def update_comment(
    session: AsyncSession,
    comment: Comment,
    *,
    content: str,
    mentioned_user_ids: list[int] | None = None,
) -> Comment:
    """Update comment content and mentions.

    Args:
        session: Database session
        comment: Comment to update
        content: New content
        mentioned_user_ids: New list of mentioned user IDs

    Returns:
        Updated comment
    """
    comment.content = content

    # Clear existing mentions and create new ones
    for mention in list(comment.mentions):
        await session.delete(mention)

    if mentioned_user_ids:
        for user_id in mentioned_user_ids:
            mention = CommentMention(comment_id=comment.id, user_id=user_id)
            session.add(mention)

    await session.flush()

    # Reload with relationships (comment exists since we just updated it)
    result = await get_comment(session, comment.id)
    assert result is not None
    return result


async def delete_comment(session: AsyncSession, comment: Comment) -> None:
    """Delete a comment (cascades to replies and mentions).

    Args:
        session: Database session
        comment: Comment to delete
    """
    await session.delete(comment)
    await session.flush()
