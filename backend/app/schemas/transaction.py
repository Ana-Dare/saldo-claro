from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    description: str = Field(min_length=1, max_length=200, examples=["Mercado"])
    amount: Decimal = Field(gt=0, decimal_places=2, examples=["150.50"])
    type: TransactionType
    date: date_type
    status: TransactionStatus
    category_id: int


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=200)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    type: TransactionType | None = None
    date: date_type | None = None
    status: TransactionStatus | None = None
    category_id: int | None = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
