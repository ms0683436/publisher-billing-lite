"""Authentication service for JWT token management and user authentication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import user_repository
from ..settings import get_settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    def __str__(self) -> str:
        return "Invalid username or password"


class InvalidTokenError(Exception):
    """Raised when token is invalid or expired."""

    def __str__(self) -> str:
        return "Invalid or expired token"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(user_id: int, username: str) -> str:
    """Create a short-lived access token.

    Args:
        user_id: The user ID to encode in the token
        username: The username to encode in the token

    Returns:
        The encoded JWT access token
    """
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "type": TOKEN_TYPE_ACCESS,
        "exp": expire,
    }
    return jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def create_refresh_token(user_id: int, username: str) -> str:
    """Create a long-lived refresh token.

    Args:
        user_id: The user ID to encode in the token
        username: The username to encode in the token

    Returns:
        The encoded JWT refresh token
    """
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "type": TOKEN_TYPE_REFRESH,
        "exp": expire,
    }
    return jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode
        expected_type: Expected token type (access or refresh)

    Returns:
        The decoded token payload

    Raises:
        InvalidTokenError: If token is invalid, expired, or wrong type
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        token_type = payload.get("type")
        if token_type != expected_type:
            raise InvalidTokenError()
        return payload
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token.

    Args:
        token: The JWT access token to decode

    Returns:
        The decoded token payload

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    return decode_token(token, TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token.

    Args:
        token: The JWT refresh token to decode

    Returns:
        The decoded token payload

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    return decode_token(token, TOKEN_TYPE_REFRESH)


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> tuple[int, str, str]:
    """Authenticate user and return tokens.

    Args:
        session: Database session
        username: Username to authenticate
        password: Password to verify

    Returns:
        Tuple of (user_id, access_token, refresh_token)

    Raises:
        InvalidCredentialsError: If username/password invalid or user inactive
    """
    user = await user_repository.get_user_by_username(session, username)

    if user is None or not user.is_active:
        raise InvalidCredentialsError()

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(user.id, user.username)

    return user.id, access_token, refresh_token


async def refresh_tokens(
    session: AsyncSession,
    refresh_token: str,
) -> tuple[int, str, str]:
    """Refresh tokens using a valid refresh token.

    Args:
        session: Database session
        refresh_token: The refresh token to validate

    Returns:
        Tuple of (user_id, new_access_token, new_refresh_token)

    Raises:
        InvalidTokenError: If refresh token is invalid or expired
        InvalidCredentialsError: If user not found or inactive
    """
    payload = decode_refresh_token(refresh_token)
    user_id = int(payload.get("sub", 0))

    user = await user_repository.get_user(session, user_id)
    if user is None or not user.is_active:
        raise InvalidCredentialsError()

    new_access_token = create_access_token(user.id, user.username)
    new_refresh_token = create_refresh_token(user.id, user.username)

    return user.id, new_access_token, new_refresh_token
