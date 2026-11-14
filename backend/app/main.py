from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION
from app.database import init_db
from app.routers import categories, dashboard, health, transactions

TAGS_METADATA = [
    {
        "name": "Categories",
        "description": "Cadastro e consulta de categorias de receita e despesa.",
    },
    {
        "name": "Transactions",
        "description": "Movimentações financeiras (receitas e despesas).",
    },
    {
        "name": "Dashboard",
        "description": "Resumo mensal, saldo atual e saldo previsto.",
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.include_router(health.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
