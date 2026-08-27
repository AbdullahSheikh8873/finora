import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreateRequest, BudgetResponse
from app.services import budget_service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetResponse])
def list_budgets(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return budget_service.list_budgets_with_usage(db, current_user.id, month, year)


@router.post("", status_code=201)
def create_budget(
    payload: BudgetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = budget_service.create_budget(db, current_user.id, payload)
    return {"id": budget.id, "detail": "Budget created."}


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget_service.delete_budget(db, current_user.id, budget_id)
    return None
