from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseByCategoryItem(BaseModel):
    category_id: int
    category_name: str
    total: Decimal = Field(decimal_places=2)


class DashboardResponse(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1, le=9999)
    total_income: Decimal = Field(decimal_places=2)
    total_expenses: Decimal = Field(decimal_places=2)
    current_balance: Decimal = Field(decimal_places=2)
    pending_expenses: Decimal = Field(decimal_places=2)
    projected_balance: Decimal = Field(decimal_places=2)
    expenses_by_category: list[ExpenseByCategoryItem]
