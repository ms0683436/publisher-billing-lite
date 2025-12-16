"""Authentication schemas for login, tokens, and user info."""

from pydantic import BaseModel, Field

from .base import BaseSchema


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login request body."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseSchema):
    """Token response for login and refresh endpoints."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class AuthUser(BaseSchema):
    """Authenticated user info."""

    id: int
    username: str
    email: str
