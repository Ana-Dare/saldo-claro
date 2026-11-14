from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Verificar se a API está no ar",
    response_description="Status da aplicação",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
