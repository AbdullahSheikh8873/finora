"""
Transfer service.

A transfer moves money between two accounts owned by the same user in a
single atomic database transaction: either both balance updates and the
transfer record are committed, or none of them are.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transfer import Transfer
from app.schemas.transaction import TransferCreateRequest
from app.services.account_service import adjust_balance, get_owned_account


def create_transfer(db: Session, user_id: uuid.UUID, payload: TransferCreateRequest) -> Transfer:
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination accounts must be different.",
        )

    from_account = get_owned_account(db, user_id, payload.from_account_id)
    to_account = get_owned_account(db, user_id, payload.to_account_id)

    if not from_account.is_active or not to_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Both accounts must be active."
        )

    try:
        adjust_balance(from_account, -payload.amount)
        adjust_balance(to_account, payload.amount)

        transfer = Transfer(
            user_id=user_id,
            from_account_id=payload.from_account_id,
            to_account_id=payload.to_account_id,
            amount=payload.amount,
            transfer_date=payload.transfer_date,
            description=payload.description,
        )
        db.add(transfer)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(transfer)
    return transfer


def list_transfers(db: Session, user_id: uuid.UUID) -> list[Transfer]:
    return list(
        db.query(Transfer)
        .filter(Transfer.user_id == user_id)
        .order_by(Transfer.transfer_date.desc(), Transfer.created_at.desc())
        .all()
    )
