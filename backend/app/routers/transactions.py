from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import TransactionStatus, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import transactions as transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar movimentação",
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    return transaction_service.create_transaction(db, payload)


@router.get(
    "",
    response_model=list[TransactionResponse],
    summary="Listar movimentações",
)
def list_transactions(
    db: Session = Depends(get_db),
    type: TransactionType | None = Query(
        default=None,
        description="Filtrar por tipo: income ou expense",
    ),
    status: TransactionStatus | None = Query(
        default=None,
        description="Filtrar por status: completed ou pending",
    ),
    category_id: int | None = Query(default=None, description="Filtrar por categoria"),
    start_date: date | None = Query(
        default=None,
        description="Data inicial (inclusive), formato AAAA-MM-DD",
    ),
    end_date: date | None = Query(
        default=None,
        description="Data final (inclusive), formato AAAA-MM-DD",
    ),
) -> list[TransactionResponse]:
    return transaction_service.list_transactions(
        db,
        type_=type,
        status=status,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Buscar movimentação por ID",
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    return transaction_service.get_transaction(db, transaction_id)


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Atualizar movimentação",
)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    return transaction_service.update_transaction(db, transaction_id, payload)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir movimentação",
)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)) -> None:
    transaction_service.delete_transaction(db, transaction_id)
