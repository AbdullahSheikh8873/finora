"""
Report / dashboard aggregation service.

Every number here is computed with SQL aggregation against PostgreSQL --
never by pulling all transactions into Python and summing in a loop.
"""
import uuid
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType


def _sum_for_period(
    db: Session, user_id: uuid.UUID, txn_type: TransactionType, start: date, end: date
) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == txn_type,
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
    )
    return Decimal(db.scalar(stmt) or 0)


def total_balance(db: Session, user_id: uuid.UUID) -> Decimal:
    stmt = select(func.coalesce(func.sum(Account.current_balance), 0)).where(
        Account.user_id == user_id, Account.is_active.is_(True)
    )
    return Decimal(db.scalar(stmt) or 0)


def savings_rate(income: Decimal, net_savings: Decimal) -> float:
    if income == 0:
        return 0.0
    return float(round((net_savings / income) * 100, 1))


def dashboard_summary(db: Session, user_id: uuid.UUID, period_start: date, period_end: date) -> dict:
    income = _sum_for_period(db, user_id, TransactionType.income, period_start, period_end)
    expenses = _sum_for_period(db, user_id, TransactionType.expense, period_start, period_end)
    net_savings = income - expenses

    prev_end = period_start - relativedelta(days=1)
    prev_start = prev_end - (period_end - period_start)
    prev_income = _sum_for_period(db, user_id, TransactionType.income, prev_start, prev_end)
    prev_expenses = _sum_for_period(db, user_id, TransactionType.expense, prev_start, prev_end)

    def pct_change(current: Decimal, previous: Decimal) -> float:
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return float(round(((current - previous) / previous) * 100, 1))

    return {
        "total_balance": total_balance(db, user_id),
        "income": income,
        "expenses": expenses,
        "net_savings": net_savings,
        "savings_rate": savings_rate(income, net_savings),
        "income_change_pct": pct_change(income, prev_income),
        "expenses_change_pct": pct_change(expenses, prev_expenses),
    }


def monthly_income_vs_expense(db: Session, user_id: uuid.UUID, months: int = 6) -> dict:
    today = date.today()
    labels, income_series, expense_series = [], [], []
    for i in range(months - 1, -1, -1):
        target = today - relativedelta(months=i)
        stmt_income = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.income,
            extract("month", Transaction.transaction_date) == target.month,
            extract("year", Transaction.transaction_date) == target.year,
        )
        stmt_expense = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.expense,
            extract("month", Transaction.transaction_date) == target.month,
            extract("year", Transaction.transaction_date) == target.year,
        )
        labels.append(target.strftime("%b %Y"))
        income_series.append(float(db.scalar(stmt_income) or 0))
        expense_series.append(float(db.scalar(stmt_expense) or 0))
    return {"labels": labels, "income": income_series, "expenses": expense_series}


def expense_breakdown(db: Session, user_id: uuid.UUID, period_start: date, period_end: date) -> dict:
    stmt = (
        select(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.expense,
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = db.execute(stmt).all()
    return {"labels": [r[0] for r in rows], "values": [float(r[1]) for r in rows]}


def cash_flow(db: Session, user_id: uuid.UUID, months: int = 6) -> dict:
    """Running total account balance movement, derived from net monthly flow."""
    series = monthly_income_vs_expense(db, user_id, months)
    running = total_balance(db, user_id)
    # Work backwards from current balance to reconstruct historical points.
    net_by_month = [i - e for i, e in zip(series["income"], series["expenses"])]
    balances = [0.0] * months
    balances[-1] = float(running)
    for idx in range(months - 2, -1, -1):
        balances[idx] = balances[idx + 1] - net_by_month[idx + 1]
    return {"labels": series["labels"], "balances": balances}
