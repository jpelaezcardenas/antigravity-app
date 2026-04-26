from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class FacturaVencidaBase(BaseModel):
    numero_factura: str
    cliente: str
    monto: float
    fecha_emision: date
    fecha_vencimiento: date
    estado: str = "no_pagada"
    intentos_cobro: int = 0

class FacturaVencida(FacturaVencidaBase):
    id: str
    usuario_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class AlertaCobro(BaseModel):
    factura_id: str
    cliente: str
    monto: float
    dias_vencidos: int
    severidad: str
    numero_factura: str

class IntentoCobroRequest(BaseModel):
    factura_id: str
    tipo_evento: str # 'recordatorio_enviado' | 'llamada' | 'carta'
    resultado: Optional[str] = None
    monto_comprometido: Optional[float] = None
    fecha_pago_comprometida: Optional[date] = None

class CartaCobroRequest(BaseModel):
    factura_id: str
    tipo: str # 'amistoso' | 'urgente' | 'pre-juridico'
