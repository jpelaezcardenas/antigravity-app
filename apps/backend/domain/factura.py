from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class FacturaVencida(BaseModel):
    id: str
    usuario_id: str
    numero_factura: str
    cliente: str
    monto: float
    fecha_emision: date
    fecha_vencimiento: date
    estado: str = 'no_pagada'
    intentos_cobro: int = 0
    created_at: datetime

class AlertaCobro(BaseModel):
    factura_id: str
    cliente: str
    dias_vencidos: int
    monto: float
    nivel_urgencia: str # 'bajo' | 'medio' | 'alto'

class IntentoCobroRequest(BaseModel):
    factura_id: str
    tipo_evento: str # 'recordatorio_enviado' | 'llamada' | 'carta'
    resultado: str
    monto_comprometido: Optional[float] = None
    fecha_pago_comprometida: Optional[date] = None

class CartaCobroRequest(BaseModel):
    factura_id: str
    tipo: str
