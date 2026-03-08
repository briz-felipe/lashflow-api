from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.user_repository import UserRepository
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


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    repo = UserRepository(session)
    user = repo.get_by_username(body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


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
def refresh(body: RefreshRequest, session: Session = Depends(get_session)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    import uuid as _uuid
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    from app.infrastructure.repositories.user_repository import UserRepository
    repo = UserRepository(session)
    user = repo.get_by_id(_uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/validate", response_model=TokenValidateResponse)
def validate_token(current_user: User = Depends(get_current_user)):
    """Validates the current access token (Bearer header) and returns user info."""
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

        import uuid as _uuid
        from app.infrastructure.repositories.user_repository import UserRepository
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
