from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import categories as category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar categoria",
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    return category_service.create_category(db, payload)


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="Listar categorias",
)
def list_categories(db: Session = Depends(get_db)) -> list[CategoryResponse]:
    return category_service.list_categories(db)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Buscar categoria por ID",
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    return category_service.get_category(db, category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Atualizar categoria",
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    return category_service.update_category(db, category_id, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir categoria",
)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    category_service.delete_category(db, category_id)
