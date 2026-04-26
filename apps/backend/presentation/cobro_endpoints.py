from fastapi import APIRouter, Depends, HTTPException
from application.cobro_service import CobroService
from domain.factura import IntentoCobroRequest, CartaCobroRequest
from presentation.pulso_endpoints import get_current_user

router = APIRouter()
cobro_service = CobroService()

@router.get("/{usuario_id}")
async def get_cartera_vencida(usuario_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/cobro/{usuario_id}
    Response: List[AlertaCobro]
    """
    return await cobro_service.monitorear_cartera_vencida(usuario_id)

@router.post("/{usuario_id}/intento")
async def registrar_intento(usuario_id: str, request: IntentoCobroRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/cobro/{usuario_id}/intento
    """
    return await cobro_service.registrar_intento_cobro(usuario_id, request.dict())

@router.post("/{usuario_id}/carta")
async def generar_carta(usuario_id: str, request: CartaCobroRequest, current_user: dict = Depends(get_current_user)):
    """
    POST /api/v1/cobro/{usuario_id}/carta
    """
    contenido = await cobro_service.generar_carta_cobro(usuario_id, request.factura_id, request.tipo)
    return {"contenido": contenido}
