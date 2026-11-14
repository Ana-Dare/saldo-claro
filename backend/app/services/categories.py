from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.name).all()


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada.",
        )
    return category


def create_category(db: Session, payload: CategoryCreate) -> Category:
    category = Category(name=payload.name, type=payload.type)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return category

    if "type" in data and data["type"] != category.type:
        incompatible = (
            db.query(Transaction)
            .filter(
                Transaction.category_id == category_id,
                Transaction.type != data["type"],
            )
            .first()
        )
        if incompatible:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não é possível alterar o tipo: existem movimentações incompatíveis.",
            )

    for key, value in data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    has_transactions = (
        db.query(Transaction).filter(Transaction.category_id == category_id).first()
    )
    if has_transactions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir: a categoria possui movimentações vinculadas.",
        )
    db.delete(category)
    db.commit()
