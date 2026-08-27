import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryType

DEFAULT_EXPENSE_CATEGORIES = [
    ("Food", "utensils", "#f97316"),
    ("Groceries", "shopping-cart", "#22c55e"),
    ("Transport", "car", "#3b82f6"),
    ("Shopping", "bag", "#ec4899"),
    ("Bills", "file-text", "#ef4444"),
    ("Utilities", "zap", "#eab308"),
    ("Rent", "home", "#8b5cf6"),
    ("Healthcare", "heart", "#14b8a6"),
    ("Education", "book", "#6366f1"),
    ("Entertainment", "film", "#f43f5e"),
    ("Travel", "plane", "#0ea5e9"),
    ("Other", "more-horizontal", "#64748b"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "briefcase", "#22c55e"),
    ("Freelance", "laptop", "#3b82f6"),
    ("Business", "trending-up", "#8b5cf6"),
    ("Investment", "bar-chart", "#14b8a6"),
    ("Gift", "gift", "#ec4899"),
    ("Other", "more-horizontal", "#64748b"),
]


def seed_default_categories(db: Session, user_id: uuid.UUID) -> None:
    for name, icon, color in DEFAULT_EXPENSE_CATEGORIES:
        db.add(Category(user_id=user_id, name=name, type=CategoryType.expense, icon=icon, color=color))
    for name, icon, color in DEFAULT_INCOME_CATEGORIES:
        db.add(Category(user_id=user_id, name=name, type=CategoryType.income, icon=icon, color=color))
    db.commit()


def list_categories(db: Session, user_id: uuid.UUID, category_type: CategoryType | None = None) -> list[Category]:
    stmt = select(Category).where(Category.user_id == user_id)
    if category_type:
        stmt = stmt.where(Category.type == category_type)
    stmt = stmt.order_by(Category.name.asc())
    return list(db.scalars(stmt).all())
