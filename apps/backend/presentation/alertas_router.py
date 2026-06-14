from fastapi import APIRouter, Depends
from typing import List
from domain.alerta import AlertaTributaria
from application.alertas_service import AlertasService
from core.deps import get_current_user, verify_resource_ownership

router = APIRouter()

@router.get("/tributarias", response_model=List[AlertaTributaria])
async def get_alertas_tributarias(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
    service: AlertasService = Depends(AlertasService)
):
    """
    GET /api/v1/centinela/tributarias?usuario_id=...

    Protected: a user can only read their own tax alerts (IDOR protection).
    """
    await verify_resource_ownership(current_user["id"], usuario_id)
    return service.obtener_alertas_umbrales(usuario_id)
