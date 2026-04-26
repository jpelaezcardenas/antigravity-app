from fastapi import APIRouter, Depends
from typing import List
from domain.alerta import AlertaTributaria
from application.alertas_service import AlertasService

router = APIRouter()

@router.get("/tributarias", response_model=List[AlertaTributaria])
async def get_alertas_tributarias(
    usuario_id: str,
    service: AlertasService = Depends(AlertasService)
):
    return service.obtener_alertas_umbrales(usuario_id)
