from __future__ import annotations

from pydantic import BaseModel, Field

from .base import BaseSchema, TimestampMixin
from .user import UserBase


class CommentResponse(BaseSchema, TimestampMixin):
    """Comment response with author and mentions"""

    id: int
    content: str
    campaign_id: int
    author: UserBase
    mentions: list[UserBase]
    parent_id: int | None
    replies: list[CommentResponse] = []
    replies_count: int = 0


class CommentCreate(BaseModel):
    """POST /api/v1/comments request body"""

    content: str = Field(..., min_length=1, max_length=5000)
    campaign_id: int
    parent_id: int | None = None


class CommentUpdate(BaseModel):
    """PUT /api/v1/comments/{id} request body"""

    content: str = Field(..., min_length=1, max_length=5000)


class CommentListResponse(BaseModel):
    """GET /api/v1/campaigns/{id}/comments response"""

    comments: list[CommentResponse]
    total: int


# Enable forward reference resolution
CommentResponse.model_rebuild()
