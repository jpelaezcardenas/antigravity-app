from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class AlertaFiscal(BaseModel):
    id: str
    usuario_id: str
    tipo: str  # 'umbral' | 'vencimiento' | 'incumplimiento'
    severidad: str  # 'roja' | 'amarilla' | 'verde'
    titulo: str
    descripcion: str
    accion_sugerida: Optional[str] = None
    fecha_limite: Optional[date] = None
    activa: bool = True
    created_at: datetime

class AlertaTributaria(BaseModel):
    nombre: str
    porcentaje: float
    valor_actual: float
    umbral: float
    severidad: str
    dias_estimados: Optional[int] = None
