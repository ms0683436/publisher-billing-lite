"""Repository utility functions."""


def escape_like_pattern(value: str) -> str:
    """Escape special characters for SQL LIKE/ILIKE patterns.

    Escapes %, _, and \\ to prevent wildcard injection.
    Use with ilike(..., escape="\\\\").
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
