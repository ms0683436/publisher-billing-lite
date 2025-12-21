"""Unit tests for authentication service."""

from __future__ import annotations

import time

import jwt
import pytest

from app.services.auth_service import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.settings import get_settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Hashing a password returns a bcrypt hash."""
        password = "password123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Verifying correct password returns True."""
        password = "password123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verifying incorrect password returns False."""
        hashed = get_password_hash("password123")

        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Same password produces different hashes (due to salt)."""
        password = "password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAccessToken:
    """Tests for access token creation and decoding."""

    def test_create_access_token(self):
        """Creates a valid access token."""
        token = create_access_token(user_id=1, username="alice")

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Decodes a valid access token."""
        token = create_access_token(user_id=42, username="bob")
        payload = decode_access_token(token)

        assert payload["sub"] == "42"
        assert payload["username"] == "bob"
        assert payload["type"] == TOKEN_TYPE_ACCESS
        assert "exp" in payload

    def test_decode_access_token_invalid(self):
        """Raises InvalidTokenError for invalid token."""
        with pytest.raises(InvalidTokenError):
            decode_access_token("invalid.token.here")

    def test_decode_access_token_wrong_type(self):
        """Raises InvalidTokenError when decoding refresh token as access."""
        refresh_token = create_refresh_token(user_id=1, username="alice")

        with pytest.raises(InvalidTokenError):
            decode_access_token(refresh_token)

    def test_access_token_contains_user_info(self):
        """Access token contains user_id and username."""
        token = create_access_token(user_id=123, username="charlie")
        settings = get_settings()

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == "123"
        assert payload["username"] == "charlie"
        assert payload["type"] == TOKEN_TYPE_ACCESS


class TestRefreshToken:
    """Tests for refresh token creation and decoding."""

    def test_create_refresh_token(self):
        """Creates a valid refresh token."""
        token = create_refresh_token(user_id=1, username="alice")

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token_valid(self):
        """Decodes a valid refresh token."""
        token = create_refresh_token(user_id=42, username="bob")
        payload = decode_refresh_token(token)

        assert payload["sub"] == "42"
        assert payload["username"] == "bob"
        assert payload["type"] == TOKEN_TYPE_REFRESH
        assert "exp" in payload

    def test_decode_refresh_token_invalid(self):
        """Raises InvalidTokenError for invalid token."""
        with pytest.raises(InvalidTokenError):
            decode_refresh_token("invalid.token.here")

    def test_decode_refresh_token_wrong_type(self):
        """Raises InvalidTokenError when decoding access token as refresh."""
        access_token = create_access_token(user_id=1, username="alice")

        with pytest.raises(InvalidTokenError):
            decode_refresh_token(access_token)


class TestTokenExpiration:
    """Tests for token expiration."""

    def test_access_token_has_expiration(self):
        """Access token has exp claim."""
        token = create_access_token(user_id=1, username="alice")
        settings = get_settings()

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert "exp" in payload
        assert payload["exp"] > time.time()

    def test_refresh_token_has_expiration(self):
        """Refresh token has exp claim."""
        token = create_refresh_token(user_id=1, username="alice")
        settings = get_settings()

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert "exp" in payload
        assert payload["exp"] > time.time()

    def test_refresh_token_expires_later_than_access(self):
        """Refresh token expires later than access token."""
        access_token = create_access_token(user_id=1, username="alice")
        refresh_token = create_refresh_token(user_id=1, username="alice")
        settings = get_settings()

        access_payload = jwt.decode(
            access_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        refresh_payload = jwt.decode(
            refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert refresh_payload["exp"] > access_payload["exp"]

    def test_expired_token_raises_error(self):
        """Decoding expired token raises InvalidTokenError."""
        settings = get_settings()

        # Create an already-expired token
        expired_payload = {
            "sub": "1",
            "username": "alice",
            "type": TOKEN_TYPE_ACCESS,
            "exp": time.time() - 100,  # Expired 100 seconds ago
        }
        expired_token = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(InvalidTokenError):
            decode_access_token(expired_token)


class TestTokenEdgeCases:
    """Tests for edge cases in token handling."""

    def test_decode_token_missing_type_field(self):
        """Raises InvalidTokenError when token has no type field."""
        settings = get_settings()

        # Token without type field
        payload = {
            "sub": "1",
            "username": "alice",
            "exp": time.time() + 3600,
        }
        token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_decode_token_empty_type_field(self):
        """Raises InvalidTokenError when token has empty type field."""
        settings = get_settings()

        payload = {
            "sub": "1",
            "username": "alice",
            "type": "",  # Empty type
            "exp": time.time() + 3600,
        }
        token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_decode_token_wrong_secret_key(self):
        """Raises InvalidTokenError when token signed with different key."""
        settings = get_settings()

        payload = {
            "sub": "1",
            "username": "alice",
            "type": TOKEN_TYPE_ACCESS,
            "exp": time.time() + 3600,
        }
        token = jwt.encode(
            payload, "wrong-secret-key", algorithm=settings.jwt_algorithm
        )

        with pytest.raises(InvalidTokenError):
            decode_access_token(token)
