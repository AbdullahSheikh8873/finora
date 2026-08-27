"""
Account service: ownership-scoped CRUD for financial accounts.

Every function takes the authenticated user's id and enforces that the
account being read/modified actually belongs to that user. This is the
one rule the whole app absolutely cannot get wrong.
"""
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreateRequest, AccountUpdateRequest


def list_accounts(db: Session, user_id: uuid.UUID, include_inactive: bool = True) -> list[Account]:
    stmt = select(Account).where(Account.user_id == user_id)
    if not include_inactive:
        stmt = stmt.where(Account.is_active.is_(True))
    stmt = stmt.order_by(Account.created_at.asc())
    return list(db.scalars(stmt).all())


def get_owned_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = db.get(Account, account_id)
    if account is None or account.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


def create_account(db: Session, user_id: uuid.UUID, payload: AccountCreateRequest) -> Account:
    account = Account(
        user_id=user_id,
        name=payload.name,
        account_type=payload.account_type,
        opening_balance=payload.opening_balance,
        current_balance=payload.opening_balance,
        currency=payload.currency,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID, payload: AccountUpdateRequest
) -> Account:
    account = get_owned_account(db, user_id, account_id)
    account.name = payload.name
    account.account_type = payload.account_type
    account.currency = payload.currency
    db.commit()
    db.refresh(account)
    return account


def archive_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = get_owned_account(db, user_id, account_id)
    account.is_active = False
    db.commit()
    db.refresh(account)
    return account


def adjust_balance(account: Account, delta: Decimal) -> None:
    """Apply a signed delta to an account's current balance in-place."""
    account.current_balance = account.current_balance + delta
