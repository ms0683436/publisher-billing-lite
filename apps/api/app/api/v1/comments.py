"""Comment API routes."""

from fastapi import APIRouter, HTTPException

from ...api.deps import CurrentUserDep, PaginationDep, SessionDep
from ...schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from ...services import ForbiddenError, NotFoundError, comment_service

router = APIRouter(tags=["comments"])


@router.get("/campaigns/{campaign_id}/comments", response_model=CommentListResponse)
async def list_campaign_comments(
    campaign_id: int,
    session: SessionDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
):
    """List comments for a campaign with nested replies."""
    try:
        return await comment_service.list_comments_for_campaign(
            session, campaign_id=campaign_id, pagination=pagination
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    data: CommentCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """Create a new comment or reply."""
    try:
        return await comment_service.create_comment(
            session, data=data, author_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """Update a comment (author only)."""
    try:
        return await comment_service.update_comment(
            session,
            comment_id=comment_id,
            content=data.content,
            current_user_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """Delete a comment (author only, cascades to replies)."""
    try:
        await comment_service.delete_comment(
            session, comment_id=comment_id, current_user_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
