import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # Cookie settings for refresh token
    cookie_secure: bool = False  # Set to True in production (requires HTTPS)
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None  # None = current domain only


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    jwt_secret_key = (os.getenv("JWT_SECRET_KEY") or "").strip()
    if not jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY environment variable is required")

    return Settings(
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
    )
