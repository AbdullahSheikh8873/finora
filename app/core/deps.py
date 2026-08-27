"""
FastAPI dependencies for retrieving the current authenticated user.

Token is read from either the httpOnly cookie (browser UI) or the
Authorization: Bearer header (API clients). Ownership checks throughout
the app rely on the `current_user.id` value returned here -- never on
any user_id supplied by the client in a form/body/query.
"""
import uuid

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, decode_access_token
from app.models.user import User


def _extract_token(request: Request, cookie_token: str | None) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    return cookie_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    finora_access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE_NAME),
) -> User:
    token = _extract_token(request, finora_access_token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    finora_access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE_NAME),
) -> User | None:
    try:
        return get_current_user(request, db, finora_access_token)
    except HTTPException:
        return None
