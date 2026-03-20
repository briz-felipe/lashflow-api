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
    ProfileUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_me(user: User) -> MeResponse:
    return MeResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
        created_at=user.created_at,
        salon_name=user.salon_name,
        salon_slug=user.salon_slug,
        salon_address=user.salon_address,
        apple_calendar_connected=bool(user.apple_id and user.apple_password_encrypted),
        apple_calendar_name=user.apple_calendar_name,
    )


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
    return _user_to_me(created)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return _user_to_me(current_user)


@router.put("/profile", response_model=MeResponse)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    repo = UserRepository(session)
    if body.salon_name is not None:
        current_user.salon_name = body.salon_name
    if body.salon_slug is not None:
        slug = body.salon_slug.strip().lower().replace(" ", "-")
        current_user.salon_slug = slug
    if body.salon_address is not None:
        current_user.salon_address = body.salon_address
    if body.maintenance_cycle_days is not None:
        current_user.maintenance_cycle_days = max(7, min(60, body.maintenance_cycle_days))
    updated = repo.update(current_user)
    return _user_to_me(updated)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: Session = Depends(get_session)):
    refresh_token_value: str | None = None

    try:
        body = await request.json()
        refresh_token_value = body.get("refresh_token")
    except Exception:
        pass

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
    return TokenValidateResponse(
        valid=True,
        user_id=current_user.id,
        username=current_user.username,
    )


@router.post("/validate", response_model=TokenValidateResponse)
def validate_token_body(body: RefreshRequest, session: Session = Depends(get_session)):
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
