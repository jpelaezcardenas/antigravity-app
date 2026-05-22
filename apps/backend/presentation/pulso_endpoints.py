from fastapi import APIRouter, Depends, HTTPException, status
from application.pulso_service import PulsoService
from core.deps import get_current_user, verify_resource_ownership

router = APIRouter()
pulso_service = PulsoService()


@router.get("/{usuario_id}")
async def get_pulso_diario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/pulso/{usuario_id}
    Response: PulsoDiario JSON
    
    Protected: User can only access their own pulso (IDOR protection).
    Admins can access any user's pulso.
    """
    verify_resource_ownership(current_user, usuario_id)

    result = await pulso_service.calcular_pulso_diario(usuario_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return result
