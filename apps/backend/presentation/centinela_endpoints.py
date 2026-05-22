from fastapi import APIRouter, Depends, HTTPException
from application.centinela_service import CentinelaService
from core.deps import get_current_user, verify_resource_ownership

router = APIRouter()
centinela_service = CentinelaService()


@router.get("/{usuario_id}")
async def get_centinela_fiscal(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/centinela/{usuario_id}
    Response: List[AlertaTributaria]
    
    Protected: User can only access their own fiscal alerts (IDOR protection).
    """
    verify_resource_ownership(current_user, usuario_id)

    return await centinela_service.evaluar_umbrales(usuario_id)
