from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class Transaccion(BaseModel):
    id: str
    usuario_id: str
    fecha: date
    tipo: str  # 'ingreso' | 'gasto'
    monto: float
    concepto: Optional[str] = None
    categoria: Optional[str] = None
    origen: Optional[str] = None # 'siigo' | 'manual' | 'stripe' | 'nequi'
    created_at: datetime

class PulsoDiario(BaseModel):
    fecha: date
    ingresos: float
    gastos: float
    margen: float
    provision_dian: float
    dinero_tuyo_hoy: float
    advertencias: list[str] = []
