from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import CategoryType, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def _ensure_category_compatible(
    db: Session,
    category_id: int,
    transaction_type: TransactionType,
) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada.",
        )

    expected = (
        CategoryType.income
        if transaction_type == TransactionType.income
        else CategoryType.expense
    )
    if category.type != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O tipo da movimentação não é compatível com o tipo da categoria.",
        )
    return category


def list_transactions(
    db: Session,
    *,
    type_: TransactionType | None = None,
    status: TransactionStatus | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Transaction]:
    query = db.query(Transaction)

    if type_ is not None:
        query = query.filter(Transaction.type == type_)
    if status is not None:
        query = query.filter(Transaction.status == status)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if start_date is not None:
        query = query.filter(Transaction.date >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.date <= end_date)

    return query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimentação não encontrada.",
        )
    return transaction


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    _ensure_category_compatible(db, payload.category_id, payload.type)
    transaction = Transaction(**payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session,
    transaction_id: int,
    payload: TransactionUpdate,
) -> Transaction:
    transaction = get_transaction(db, transaction_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return transaction

    new_type = data.get("type", transaction.type)
    new_category_id = data.get("category_id", transaction.category_id)
    _ensure_category_compatible(db, new_category_id, new_type)

    for key, value in data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int) -> None:
    transaction = get_transaction(db, transaction_id)
    db.delete(transaction)
    db.commit()
