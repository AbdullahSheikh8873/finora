from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserPublic
from app.schemas.user import PreferencesUpdateRequest, ProfileUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.put("/me", response_model=UserPublic)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.email.lower() != current_user.email:
        existing = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use.")
    current_user.full_name = payload.full_name
    current_user.email = payload.email.lower()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/preferences", response_model=UserPublic)
def update_preferences(
    payload: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.currency = payload.currency
    current_user.date_format = payload.date_format
    current_user.theme = payload.theme
    db.commit()
    db.refresh(current_user)
    return current_user
