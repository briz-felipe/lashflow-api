import uuid as _uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.settings import settings
from app.domain.entities.user import User
from app.interface.dependencies import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_superuser,
)
from app.interface.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    TokenValidateResponse,
    MeResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_DAYS * 86400,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def token(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """OAuth2 form-data endpoint used by Swagger UI and machine clients (e.g. Next.js BFF).

    If OAUTH2_CLIENT_ID and OAUTH2_CLIENT_SECRET are set in the environment, the request
    must supply matching client_id and client_secret fields (standard OAuth2 password grant).
    Leave those env vars unset to skip client validation (useful for Swagger UI / local dev).
    """
    if settings.oauth2_client_auth_enabled:
        if form.client_id != settings.OAUTH2_CLIENT_ID or form.client_secret != settings.OAUTH2_CLIENT_SECRET:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")

    repo = UserRepository(session)
    user = repo.get_by_username(form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, session: Session = Depends(get_session)):
    if settings.oauth2_client_auth_enabled:
        if body.client_id != settings.OAUTH2_CLIENT_ID or body.client_secret != settings.OAUTH2_CLIENT_SECRET:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")

    repo = UserRepository(session)
    user = repo.get_by_username(body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
def logout(response: Response):
    """Clears auth cookies. Works for both cookie-based and header-based sessions."""
    _clear_auth_cookies(response)


@router.post("/register", response_model=MeResponse, status_code=201)
def register(
    body: RegisterRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_superuser),
):
    repo = UserRepository(session)
    if repo.get_by_username(body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    if body.email and repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    created = repo.create(user)
    return MeResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        is_superuser=created.is_superuser,
        is_active=created.is_active,
        created_at=created.created_at,
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: Session = Depends(get_session)):
    """Exchange a valid refresh token for a new access + refresh token pair.

    Accepts the token from either:
    - JSON body: { "refresh_token": "eyJ..." }
    - Cookie: refresh_token (set automatically on login)
    """
    refresh_token_value: str | None = None

    # Try JSON body first
    try:
        body = await request.json()
        refresh_token_value = body.get("refresh_token")
    except Exception:
        pass

    # Fall back to cookie
    if not refresh_token_value:
        refresh_token_value = request.cookies.get("refresh_token")

    if not refresh_token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

    try:
        payload = decode_token(refresh_token_value)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    repo = UserRepository(session)
    user = repo.get_by_id(_uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, new_refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/validate", response_model=TokenValidateResponse)
def validate_token(current_user: User = Depends(get_current_user)):
    """Validates the current access token (Bearer header or cookie) and returns user info."""
    return TokenValidateResponse(
        valid=True,
        user_id=current_user.id,
        username=current_user.username,
    )


@router.post("/validate", response_model=TokenValidateResponse)
def validate_token_body(body: RefreshRequest, session: Session = Depends(get_session)):
    """Validates any token (access or refresh) passed in the body. Returns validity + expiry."""
    try:
        payload = decode_token(body.refresh_token)
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
        user_id = payload.get("sub")

        repo = UserRepository(session)
        user = repo.get_by_id(_uuid.UUID(user_id)) if user_id else None

        return TokenValidateResponse(
            valid=True,
            user_id=user.id if user else None,
            username=user.username if user else None,
            expires_at=expires_at,
        )
    except JWTError:
        return TokenValidateResponse(valid=False)
