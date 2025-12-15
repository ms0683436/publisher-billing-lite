"""Service for parsing and resolving @mentions in comment content."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import user_repository

if TYPE_CHECKING:
    from ..models import User


# Match @username (ASCII letters/digits/underscore, 1-50 chars).
# Require start-of-string or whitespace before '@' to avoid matching emails like "a@b.com".
# Disallow longer usernames by requiring a non-username char boundary after the match.
MENTION_PATTERN = re.compile(r"(?<!\S)@([A-Za-z0-9_]{1,50})(?![A-Za-z0-9_])")


def parse_mentions(content: str) -> list[str]:
    """Extract unique @usernames from content.

    Args:
        content: Comment content text

    Returns:
        List of unique usernames (without @ prefix)
    """
    matches = MENTION_PATTERN.findall(content)
    # Return unique usernames, preserving order
    seen: set[str] = set()
    result: list[str] = []
    for username in matches:
        lower = username.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(username)
    return result


async def resolve_mentions(
    session: AsyncSession,
    usernames: list[str],
) -> tuple[list[User], list[str]]:
    """Resolve usernames to User objects.

    Args:
        session: Database session
        usernames: List of usernames to resolve

    Returns:
        Tuple of (found_users, unresolved_usernames)
    """
    if not usernames:
        return [], []

    users = await user_repository.get_users_by_usernames(session, usernames)
    found_names = {u.username.lower() for u in users}
    unresolved = [u for u in usernames if u.lower() not in found_names]

    return users, unresolved
