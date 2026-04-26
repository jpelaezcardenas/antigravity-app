from fastapi import APIRouter, Depends, Query
from datetime import date
from domain.transaccion import PulsoDiario
from application.pulso_service import PulsoService

router = APIRouter()

@router.get("/diario", response_model=PulsoDiario)
async def get_pulso_diario(
    usuario_id: str, 
    fecha: date = Query(default=date.today()),
    service: PulsoService = Depends(PulsoService)
):
    return service.calcular_pulso_diario(usuario_id, fecha)
