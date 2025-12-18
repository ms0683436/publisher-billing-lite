"""Notification API routes."""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ...api.deps import CurrentUserDep, SessionDep
from ...schemas.notification import (
    NotificationListResponse,
    NotificationReadResponse,
)
from ...services import ForbiddenError, NotFoundError, notification_service
from ...services.notification_broadcaster import get_broadcaster

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(5, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """List notifications for the current user."""
    return await notification_service.list_notifications(
        session, user_id=current_user.id, limit=limit, offset=offset
    )


@router.patch("/{notification_id}/read", response_model=NotificationReadResponse)
async def mark_notification_read(
    notification_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """Mark a single notification as read."""
    try:
        return await notification_service.mark_as_read(
            session, notification_id=notification_id, current_user_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.patch("/read-all", response_model=NotificationReadResponse)
async def mark_all_notifications_read(
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """Mark all notifications for the current user as read."""
    return await notification_service.mark_all_as_read(
        session, current_user_id=current_user.id
    )


@router.get("/stream")
async def notification_stream(
    current_user: CurrentUserDep,
):
    """SSE endpoint for real-time notifications.

    Streams notifications as Server-Sent Events.
    Connect using EventSource in the browser.
    """
    broadcaster = get_broadcaster()

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from Redis Pub/Sub."""
        async with broadcaster.subscribe(current_user.id) as messages:
            async for message in messages:
                if message.get("type") == "heartbeat":
                    # Send comment to keep connection alive
                    yield ": heartbeat\n\n"
                else:
                    # Send notification data
                    yield f"data: {json.dumps(message)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
