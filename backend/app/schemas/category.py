from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CategoryType


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80, examples=["Salário"])
    type: CategoryType


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: CategoryType | None = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
