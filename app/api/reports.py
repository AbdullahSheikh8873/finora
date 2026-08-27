from datetime import date

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _resolve_period(period: str, date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = date.today()
    if period == "this_month":
        start = today.replace(day=1)
        end = today
    elif period == "last_month":
        first_this_month = today.replace(day=1)
        end = first_this_month - relativedelta(days=1)
        start = end.replace(day=1)
    elif period == "last_3_months":
        start = today - relativedelta(months=3)
        end = today
    elif period == "last_6_months":
        start = today - relativedelta(months=6)
        end = today
    elif period == "this_year":
        start = today.replace(month=1, day=1)
        end = today
    elif period == "custom" and date_from and date_to:
        start, end = date_from, date_to
    else:
        start = today.replace(day=1)
        end = today
    return start, end


@router.get("/summary")
def report_summary(
    period: str = Query("this_month"),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _resolve_period(period, date_from, date_to)
    summary = report_service.dashboard_summary(db, current_user.id, start, end)
    breakdown = report_service.expense_breakdown(db, current_user.id, start, end)
    return {
        "period_start": start,
        "period_end": end,
        "summary": summary,
        "expense_breakdown": breakdown,
    }


@router.get("/dashboard")
def dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    start = today.replace(day=1)
    summary = report_service.dashboard_summary(db, current_user.id, start, today)
    trend = report_service.monthly_income_vs_expense(db, current_user.id, months=6)
    breakdown = report_service.expense_breakdown(db, current_user.id, start, today)
    flow = report_service.cash_flow(db, current_user.id, months=6)
    return {
        "summary": summary,
        "trend": trend,
        "expense_breakdown": breakdown,
        "cash_flow": flow,
    }
