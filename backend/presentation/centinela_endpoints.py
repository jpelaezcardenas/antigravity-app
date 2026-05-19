from fastapi import APIRouter, Depends, HTTPException
from application.centinela_service import CentinelaService
from presentation.pulso_endpoints import get_current_user

router = APIRouter()
centinela_service = CentinelaService()

@router.get("/{usuario_id}")
async def get_centinela_fiscal(usuario_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/centinela/{usuario_id}
    Response: List[AlertaTributaria]
    """
    return await centinela_service.evaluar_umbrales(usuario_id)
