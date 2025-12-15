from pydantic import BaseModel

from .base import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base User fields for API responses"""

    id: int
    username: str


class UserDetail(UserBase, TimestampMixin):
    """GET /api/v1/users/{id} detail response"""

    email: str
    is_active: bool


class UserListResponse(BaseModel):
    """GET /api/v1/users response"""

    users: list[UserBase]
    total: int
