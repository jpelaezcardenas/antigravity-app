from fastapi import APIRouter, Depends, HTTPException, status
from application.pulso_service import PulsoService
from core.security import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
pulso_service = PulsoService()
security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(auth.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    return payload

@router.get("/{usuario_id}")
async def get_pulso_diario(usuario_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/v1/pulso/{usuario_id}
    Response: PulsoDiario JSON
    """
    # Seguridad básica: el usuario solo puede pedir su propio pulso (o si es admin)
    # Para la demo permitimos si el token es válido
    
    result = await pulso_service.calcular_pulso_diario(usuario_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return result
