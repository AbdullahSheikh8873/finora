import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.transaction import TransactionType


class TransactionCreateRequest(BaseModel):
    transaction_type: TransactionType
    amount: Decimal
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    transaction_date: date
    description: str
    reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return v

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Description is required.")
        return v


class TransactionUpdateRequest(TransactionCreateRequest):
    pass


class TransactionResponse(BaseModel):
    id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID]
    transaction_date: date
    description: str
    reference: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransferCreateRequest(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    transfer_date: date
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return v
