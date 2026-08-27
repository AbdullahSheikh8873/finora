import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.models.account import AccountType


class AccountCreateRequest(BaseModel):
    name: str
    account_type: AccountType
    opening_balance: Decimal = Decimal("0.00")
    currency: str = "PKR"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Account name is required.")
        return v


class AccountUpdateRequest(BaseModel):
    name: str
    account_type: AccountType
    currency: str = "PKR"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Account name is required.")
        return v


class AccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    account_type: AccountType
    opening_balance: Decimal
    current_balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
