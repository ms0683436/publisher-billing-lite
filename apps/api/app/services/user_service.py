from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import Pagination
from ..repositories import user_repository
from ..schemas.user import UserBase, UserDetail, UserListResponse
from .errors import NotFoundError


async def list_users(
    session: AsyncSession,
    *,
    pagination: Pagination,
) -> UserListResponse:
    """List users with pagination.

    Args:
        session: Database session
        pagination: Pagination parameters

    Returns:
        UserListResponse with users and total count
    """
    users, total = await user_repository.list_users(
        session, limit=pagination.limit, offset=pagination.offset
    )

    return UserListResponse(
        users=[UserBase.model_validate(user) for user in users],
        total=total,
    )


async def get_user_detail(
    session: AsyncSession,
    *,
    user_id: int,
) -> UserDetail:
    """Get user detail by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        UserDetail

    Raises:
        NotFoundError: If user not found
    """
    user = await user_repository.get_user(session, user_id)
    if user is None:
        raise NotFoundError("user", user_id)

    return UserDetail.model_validate(user)


async def search_users(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 10,
) -> UserListResponse:
    """Search users by username for @mention autocomplete.

    Args:
        session: Database session
        query: Search query string
        limit: Maximum number of results

    Returns:
        UserListResponse with matching users
    """
    users = await user_repository.search_users(session, query, limit=limit)

    return UserListResponse(
        users=[UserBase.model_validate(user) for user in users],
        total=len(users),
    )
