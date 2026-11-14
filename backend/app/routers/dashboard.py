from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Resumo financeiro do mês",
    description=(
        "Considera apenas movimentações com data no mês/ano informados. "
        "Receitas e despesas concluídas entram no saldo atual; "
        "despesas pendentes reduzem o saldo previsto."
    ),
)
def get_dashboard(
    db: Session = Depends(get_db),
    month: int = Query(..., ge=1, le=12, description="Mês (1 a 12)"),
    year: int = Query(..., ge=1, le=9999, description="Ano com quatro dígitos"),
) -> DashboardResponse:
    return dashboard_service.get_dashboard(db, month, year)
