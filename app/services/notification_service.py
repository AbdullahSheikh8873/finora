"""
Notification service: create and manage in-app notifications.

Notification-triggering business events (budget nearing/exceeding limit,
large expense, new account) call `create_notification` from the relevant
service/route after the triggering write has been committed.
"""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType

LARGE_EXPENSE_THRESHOLD = Decimal("50000")


def create_notification(
    db: Session, user_id: uuid.UUID, title: str, message: str, ntype: NotificationType
) -> Notification:
    notification = Notification(user_id=user_id, title=title, message=message, type=ntype)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(db: Session, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc())
    return list(db.scalars(stmt).all())


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return len(list_notifications(db, user_id, unread_only=True))


def mark_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    for n in list_notifications(db, user_id, unread_only=True):
        n.is_read = True
    db.commit()


def maybe_notify_large_expense(db: Session, user_id: uuid.UUID, amount: Decimal, description: str) -> None:
    if amount >= LARGE_EXPENSE_THRESHOLD:
        create_notification(
            db,
            user_id,
            title="Large expense recorded",
            message=f"A large expense of {amount:.2f} was recorded for '{description}'.",
            ntype=NotificationType.large_expense,
        )


def maybe_notify_budget_status(db: Session, user_id: uuid.UUID, category_name: str, status_label: str) -> None:
    if status_label == "critical":
        create_notification(
            db,
            user_id,
            title="Budget exceeded",
            message=f"Your '{category_name}' budget has been exceeded.",
            ntype=NotificationType.budget_exceeded,
        )
    elif status_label == "warning":
        create_notification(
            db,
            user_id,
            title="Budget nearing limit",
            message=f"Your '{category_name}' budget is close to its limit.",
            ntype=NotificationType.budget_warning,
        )
