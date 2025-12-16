"""Authentication routes for login, logout, and token refresh."""

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from ...api.deps import CurrentUserDep, SessionDep
from ...schemas import AuthUser, LoginRequest, TokenResponse
from ...services import NotFoundError, auth_service, user_service
from ...services.auth_service import InvalidCredentialsError, InvalidTokenError
from ...settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE = "refresh_token"


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """Set refresh token as HttpOnly cookie."""
    settings = get_settings()
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/api/v1/auth/refresh",
    )


def _clear_refresh_token_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    settings = get_settings()
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/api/v1/auth/refresh",
    )


@router.post("/login", response_model=TokenResponse)
async def login(session: SessionDep, credentials: LoginRequest, response: Response):
    """Authenticate user and return access token. Refresh token is set as HttpOnly cookie."""
    try:
        user_id, access_token, refresh_token = await auth_service.authenticate_user(
            session,
            credentials.username,
            credentials.password,
        )
        settings = get_settings()

        # Set refresh token as HttpOnly cookie
        _set_refresh_token_cookie(response, refresh_token)

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    session: SessionDep,
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE),
):
    """Refresh tokens using refresh token from HttpOnly cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        (
            user_id,
            new_access_token,
            new_refresh_token,
        ) = await auth_service.refresh_tokens(
            session,
            refresh_token,
        )
        settings = get_settings()

        # Update refresh token cookie
        _set_refresh_token_cookie(response, new_refresh_token)

        return TokenResponse(
            access_token=new_access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    except (InvalidTokenError, InvalidCredentialsError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/logout")
async def logout(response: Response):
    """Logout by clearing the refresh token cookie.

    JWT access token is stateless, so client should also discard it.
    """
    _clear_refresh_token_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=AuthUser)
async def get_current_user_info(session: SessionDep, current_user: CurrentUserDep):
    """Get current authenticated user info (queries database for full details)."""
    try:
        user = await user_service.get_user_detail(session, user_id=current_user.id)
        return AuthUser(
            id=user.id,
            username=user.username,
            email=user.email,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
