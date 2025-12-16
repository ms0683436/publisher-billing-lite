from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User


async def list_users(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> tuple[list[User], int]:
    """List users with pagination.

    Args:
        session: Database session
        limit: Maximum number of users to return
        offset: Number of users to skip

    Returns:
        Tuple of (users list, total count)
    """
    # Get total count
    count_stmt = select(func.count(User.id))
    total = (await session.execute(count_stmt)).scalar_one()

    # Get paginated users
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.username)
        .limit(limit)
        .offset(offset)
    )
    users = list((await session.execute(stmt)).scalars().all())

    return users, total


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Get user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        User instance or None if not found
    """
    stmt = select(User).where(User.id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Get user by username (case-insensitive).

    Args:
        session: Database session
        username: Username to look up

    Returns:
        User instance or None if not found
    """
    stmt = select(User).where(func.lower(User.username) == username.lower())
    return (await session.execute(stmt)).scalar_one_or_none()


async def search_users(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 10,
) -> list[User]:
    """Search users by username (case-insensitive prefix match).

    Used for @mention autocomplete.

    Args:
        session: Database session
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of matching users
    """
    pattern = f"{query.lower()}%"
    stmt = (
        select(User)
        .where(
            User.is_active.is_(True),
            func.lower(User.username).like(pattern),
        )
        .order_by(User.username)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_users_by_usernames(
    session: AsyncSession,
    usernames: list[str],
) -> list[User]:
    """Get users by a list of usernames (case-insensitive).

    Used for resolving @mentions in comment content.

    Args:
        session: Database session
        usernames: List of usernames to look up

    Returns:
        List of found users
    """
    if not usernames:
        return []

    # Case-insensitive match
    lower_usernames = [u.lower() for u in usernames]
    stmt = select(User).where(
        User.is_active.is_(True),
        func.lower(User.username).in_(lower_usernames),
    )
    return list((await session.execute(stmt)).scalars().all())
