import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.services import transaction_service
from app.services.budget_service import _budget_status, _spent_for_category
from app.services.notification_service import maybe_notify_budget_status, maybe_notify_large_expense

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    search: str | None = None,
    transaction_type: TransactionType | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = transaction_service.TransactionFilter(
        search=search,
        transaction_type=transaction_type,
        category_id=category_id,
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    items, total = transaction_service.list_transactions(db, current_user.id, filters)
    return {
        "items": [TransactionResponse.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _post_create_notifications(db, user_id, payload):
    maybe_notify_large_expense(db, user_id, payload.amount, payload.description)
    if payload.category_id and payload.transaction_type == TransactionType.expense:
        from app.models.budget import Budget

        today = payload.transaction_date
        budget = (
            db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.category_id == payload.category_id,
                Budget.month == today.month,
                Budget.year == today.year,
            )
            .first()
        )
        if budget:
            spent = _spent_for_category(db, user_id, payload.category_id, today.month, today.year)
            ratio = (spent / budget.amount) if budget.amount > 0 else 0
            status_label = _budget_status(ratio)
            maybe_notify_budget_status(db, user_id, budget.category.name, status_label)


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    payload: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = transaction_service.create_transaction(db, current_user.id, payload)
    _post_create_notifications(db, current_user.id, payload)
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = transaction_service.update_transaction(db, current_user.id, transaction_id, payload)
    _post_create_notifications(db, current_user.id, payload)
    return txn


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction_service.delete_transaction(db, current_user.id, transaction_id)
    return None
