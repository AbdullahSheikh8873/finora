"""
Transaction service.

Central rule: an income transaction increases its account's balance, an
expense transaction decreases it. Editing or deleting a transaction must
exactly reverse its prior effect before applying the new one, so balances
never drift and nothing is double-counted.
"""
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreateRequest, TransactionUpdateRequest
from app.services.account_service import adjust_balance, get_owned_account


def _signed_delta(transaction_type: TransactionType, amount: Decimal) -> Decimal:
    return amount if transaction_type == TransactionType.income else -amount


def get_owned_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    txn = db.get(Transaction, transaction_id)
    if txn is None or txn.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return txn


def _validate_category(db: Session, user_id: uuid.UUID, category_id: Optional[uuid.UUID]) -> None:
    if category_id is None:
        return
    category = db.get(Category, category_id)
    if category is None or category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category.")


def create_transaction(
    db: Session, user_id: uuid.UUID, payload: TransactionCreateRequest
) -> Transaction:
    account = get_owned_account(db, user_id, payload.account_id)
    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is archived.")
    _validate_category(db, user_id, payload.category_id)

    txn = Transaction(
        user_id=user_id,
        account_id=payload.account_id,
        category_id=payload.category_id,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        description=payload.description,
        transaction_date=payload.transaction_date,
        reference=payload.reference,
        notes=payload.notes,
    )
    db.add(txn)
    adjust_balance(account, _signed_delta(payload.transaction_type, payload.amount))
    db.commit()
    db.refresh(txn)
    return txn


def update_transaction(
    db: Session,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdateRequest,
) -> Transaction:
    txn = get_owned_transaction(db, user_id, transaction_id)
    _validate_category(db, user_id, payload.category_id)
    new_account = get_owned_account(db, user_id, payload.account_id)

    # Reverse the old effect on the old account.
    old_account = db.get(Account, txn.account_id)
    if old_account is not None:
        adjust_balance(old_account, -_signed_delta(txn.transaction_type, txn.amount))

    # Apply the new effect on the (possibly different) new account.
    adjust_balance(new_account, _signed_delta(payload.transaction_type, payload.amount))

    txn.account_id = payload.account_id
    txn.category_id = payload.category_id
    txn.transaction_type = payload.transaction_type
    txn.amount = payload.amount
    txn.description = payload.description
    txn.transaction_date = payload.transaction_date
    txn.reference = payload.reference
    txn.notes = payload.notes

    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    txn = get_owned_transaction(db, user_id, transaction_id)
    account = db.get(Account, txn.account_id)
    if account is not None:
        adjust_balance(account, -_signed_delta(txn.transaction_type, txn.amount))
    db.delete(txn)
    db.commit()


@dataclass
class TransactionFilter:
    search: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    category_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    page_size: int = 25


def list_transactions(
    db: Session, user_id: uuid.UUID, filters: TransactionFilter
) -> tuple[list[Transaction], int]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)

    if filters.search:
        like = f"%{filters.search}%"
        stmt = stmt.join(Category, Transaction.category_id == Category.id, isouter=True).where(
            or_(
                Transaction.description.ilike(like),
                Transaction.reference.ilike(like),
                Category.name.ilike(like),
            )
        )
    if filters.transaction_type:
        stmt = stmt.where(Transaction.transaction_type == filters.transaction_type)
    if filters.category_id:
        stmt = stmt.where(Transaction.category_id == filters.category_id)
    if filters.account_id:
        stmt = stmt.where(Transaction.account_id == filters.account_id)
    if filters.date_from:
        stmt = stmt.where(Transaction.transaction_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Transaction.transaction_date <= filters.date_to)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = (
        stmt.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    items = list(db.scalars(stmt).unique().all())
    return items, total
