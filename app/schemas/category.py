import uuid

from pydantic import BaseModel, field_validator

from app.models.category import CategoryType


class CategoryCreateRequest(BaseModel):
    name: str
    type: CategoryType
    icon: str = "tag"
    color: str = "#6366f1"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Category name is required.")
        return v


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: CategoryType
    icon: str
    color: str

    model_config = {"from_attributes": True}
