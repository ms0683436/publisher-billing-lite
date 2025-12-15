from fastapi import APIRouter, HTTPException, Query

from ...api.deps import PaginationDep, SessionDep
from ...schemas.user import UserDetail, UserListResponse
from ...services import NotFoundError, user_service

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserListResponse)
async def list_users(session: SessionDep, pagination: PaginationDep):
    """List all active users."""
    return await user_service.list_users(session, pagination=pagination)


@router.get("/users/search", response_model=UserListResponse)
async def search_users(
    session: SessionDep,
    q: str = Query(..., min_length=1, description="Search query for username"),
):
    """Search users by username (for @mention autocomplete)."""
    return await user_service.search_users(session, query=q)


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(user_id: int, session: SessionDep):
    """Get user details by ID."""
    try:
        return await user_service.get_user_detail(session, user_id=user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
