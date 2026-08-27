import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import transaction_service

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/transactions.csv")
def export_transactions_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = transaction_service.TransactionFilter(
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        category_id=category_id,
        page=1,
        page_size=1_000_000,
    )
    items, _total = transaction_service.list_transactions(db, current_user.id, filters)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Description", "Category", "Account", "Type", "Amount", "Notes"])
    for t in items:
        writer.writerow(
            [
                t.transaction_date.isoformat(),
                t.description,
                t.category.name if t.category else "",
                t.account.name if t.account else "",
                t.transaction_type.value,
                f"{t.amount:.2f}",
                t.notes or "",
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finora_transactions.csv"},
    )
