import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.account import AccountCreateRequest, AccountResponse, AccountUpdateRequest
from app.services import account_service
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return account_service.list_accounts(db, current_user.id)


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(
    payload: AccountCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = account_service.create_account(db, current_user.id, payload)
    create_notification(
        db,
        current_user.id,
        title="New account created",
        message=f"Account '{account.name}' was created.",
        ntype=NotificationType.account_created,
    )
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.get_owned_account(db, current_user.id, account_id)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.update_account(db, current_user.id, account_id, payload)


@router.post("/{account_id}/archive", response_model=AccountResponse)
def archive_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.archive_account(db, current_user.id, account_id)
