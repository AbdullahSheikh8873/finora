import uuid
from decimal import Decimal

from pydantic import BaseModel, field_validator


class BudgetCreateRequest(BaseModel):
    category_id: uuid.UUID
    amount: Decimal
    month: int
    year: int

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Budget amount must be greater than zero.")
        return v

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12.")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if not 2000 <= v <= 2100:
            raise ValueError("Year must be a reasonable value.")
        return v


class BudgetResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    usage_percent: float
    status: str
    month: int
    year: int

    model_config = {"from_attributes": True}
