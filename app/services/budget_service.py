"""
Budget service.

Budget "spent" is always computed live from the transactions table via
SQL aggregation -- it is never stored, so it can't drift out of sync.
"""
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import BudgetCreateRequest, BudgetResponse

WARNING_THRESHOLD = Decimal("0.70")
CRITICAL_THRESHOLD = Decimal("0.90")


def _budget_status(usage_ratio: Decimal) -> str:
    if usage_ratio >= CRITICAL_THRESHOLD:
        return "critical"
    if usage_ratio >= WARNING_THRESHOLD:
        return "warning"
    return "safe"


def _spent_for_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, month: int, year: int) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.transaction_type == TransactionType.expense,
        extract("month", Transaction.transaction_date) == month,
        extract("year", Transaction.transaction_date) == year,
    )
    return Decimal(db.scalar(stmt) or 0)


def create_budget(db: Session, user_id: uuid.UUID, payload: BudgetCreateRequest) -> Budget:
    category = db.get(Category, payload.category_id)
    if category is None or category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category.")

    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == payload.category_id,
        Budget.month == payload.month,
        Budget.year == payload.year,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A budget for this category and period already exists.",
        )

    budget = Budget(
        user_id=user_id,
        category_id=payload.category_id,
        amount=payload.amount,
        month=payload.month,
        year=payload.year,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_owned_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget:
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    return budget


def delete_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
    budget = get_owned_budget(db, user_id, budget_id)
    db.delete(budget)
    db.commit()


def list_budgets_with_usage(
    db: Session, user_id: uuid.UUID, month: int, year: int
) -> list[BudgetResponse]:
    budgets = (
        db.query(Budget)
        .filter(Budget.user_id == user_id, Budget.month == month, Budget.year == year)
        .all()
    )
    results: list[BudgetResponse] = []
    for b in budgets:
        spent = _spent_for_category(db, user_id, b.category_id, month, year)
        remaining = b.amount - spent
        usage_ratio = (spent / b.amount) if b.amount > 0 else Decimal(0)
        results.append(
            BudgetResponse(
                id=b.id,
                category_id=b.category_id,
                category_name=b.category.name,
                amount=b.amount,
                spent=spent,
                remaining=remaining,
                usage_percent=float(round(usage_ratio * 100, 1)),
                status=_budget_status(usage_ratio),
                month=b.month,
                year=b.year,
            )
        )
    return results
