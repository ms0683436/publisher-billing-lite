from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """User info extracted from JWT token (no database query needed)."""

    id: int
    username: str


@dataclass(frozen=True, slots=True)
class Pagination:
    limit: int
    offset: int


def get_pagination(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


@dataclass(frozen=True, slots=True)
class SearchParams:
    search: str | None


def get_search_params(
    search: str | None = Query(None, min_length=1, max_length=100),
) -> SearchParams:
    return SearchParams(search=search)


SearchDep = Annotated[SearchParams, Depends(get_search_params)]


@dataclass(frozen=True, slots=True)
class CampaignSortParams:
    sort_by: (
        Literal[
            "id",
            "name",
            "total_booked",
            "total_actual",
            "total_billable",
            "line_items_count",
        ]
        | None
    )
    sort_dir: SortDirection


def get_campaign_sort_params(
    sort_by: (
        Literal[
            "id",
            "name",
            "total_booked",
            "total_actual",
            "total_billable",
            "line_items_count",
        ]
        | None
    ) = Query(None),
    sort_dir: SortDirection = Query(SortDirection.asc),  # noqa: B008
) -> CampaignSortParams:
    return CampaignSortParams(sort_by=sort_by, sort_dir=sort_dir)


CampaignSortDep = Annotated[CampaignSortParams, Depends(get_campaign_sort_params)]


@dataclass(frozen=True, slots=True)
class InvoiceSortParams:
    sort_by: Literal["id", "campaign_name", "total_billable", "line_items_count"] | None
    sort_dir: SortDirection


def get_invoice_sort_params(
    sort_by: Literal["id", "campaign_name", "total_billable", "line_items_count"]
    | None = Query(None),
    sort_dir: SortDirection = Query(SortDirection.asc),  # noqa: B008
) -> InvoiceSortParams:
    return InvoiceSortParams(sort_by=sort_by, sort_dir=sort_dir)


InvoiceSortDep = Annotated[InvoiceSortParams, Depends(get_invoice_sort_params)]


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),  # noqa: B008
) -> AuthenticatedUser:
    """Extract and validate JWT access token, return current user info.

    User info is extracted directly from JWT payload (no database query).

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        AuthenticatedUser with id and username from JWT

    Raises:
        HTTPException 401: If token missing or invalid
    """
    # Import here to avoid circular import
    from ..services import auth_service
    from ..services.auth_service import InvalidTokenError

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = auth_service.decode_access_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = int(payload.get("sub", 0))
    username = payload.get("username", "")

    return AuthenticatedUser(id=user_id, username=username)


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]

__all__ = [
    "get_session",
    "SessionDep",
    "AsyncSession",
    "Pagination",
    "get_pagination",
    "PaginationDep",
    "SortDirection",
    "SearchParams",
    "get_search_params",
    "SearchDep",
    "CampaignSortParams",
    "get_campaign_sort_params",
    "CampaignSortDep",
    "InvoiceSortParams",
    "get_invoice_sort_params",
    "InvoiceSortDep",
    "AuthenticatedUser",
    "CurrentUserDep",
    "get_current_user",
]
