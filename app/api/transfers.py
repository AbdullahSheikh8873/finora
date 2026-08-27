from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.transaction import TransferCreateRequest
from app.services import transfer_service

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


@router.get("")
def list_transfers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transfers = transfer_service.list_transfers(db, current_user.id)
    return [
        {
            "id": t.id,
            "from_account_id": t.from_account_id,
            "to_account_id": t.to_account_id,
            "amount": t.amount,
            "transfer_date": t.transfer_date,
            "description": t.description,
        }
        for t in transfers
    ]


@router.post("", status_code=201)
def create_transfer(
    payload: TransferCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transfer = transfer_service.create_transfer(db, current_user.id, payload)
    return {
        "id": transfer.id,
        "from_account_id": transfer.from_account_id,
        "to_account_id": transfer.to_account_id,
        "amount": transfer.amount,
        "transfer_date": transfer.transfer_date,
        "description": transfer.description,
    }
