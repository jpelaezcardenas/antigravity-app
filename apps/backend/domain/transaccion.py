from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class TransaccionBase(BaseModel):
    fecha: date
    tipo: str  # 'ingreso' | 'gasto'
    monto: float
    concepto: Optional[str] = None
    categoria: Optional[str] = "general"
    origen: Optional[str] = "manual"

class TransaccionCreate(TransaccionBase):
    usuario_id: str

class Transaccion(TransaccionBase):
    id: str
    usuario_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class PulsoDiario(BaseModel):
    fecha: date
    ingresos_hoy: float
    gastos_hoy: float
    margen_hoy: float
    provision_dian: float
    dinero_tuyo_hoy: float
    advertencias: list[str] = []
