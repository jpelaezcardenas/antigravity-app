from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class AlertaFiscalBase(BaseModel):
    tipo: str  # 'umbral' | 'vencimiento' | 'incumplimiento'
    severidad: str  # 'roja' | 'amarilla' | 'verde'
    titulo: str
    descripcion: Optional[str] = None
    accion_sugerida: Optional[str] = None
    fecha_limite: Optional[date] = None
    activa: bool = True

class AlertaFiscal(AlertaFiscalBase):
    id: str
    usuario_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class AlertaTributaria(BaseModel):
    impuesto: str # 'Renta' | 'IVA'
    porcentaje_uso: float
    valor_actual: float
    umbral: float
    severidad: str
    mensaje: str
    dias_estimados_para_cruce: Optional[int] = None
