from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.category import CategoryType
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryResponse
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    type: CategoryType | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return category_service.list_categories(db, current_user.id, type)


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.category import Category

    category = Category(
        user_id=current_user.id,
        name=payload.name,
        type=payload.type,
        icon=payload.icon,
        color=payload.color,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
