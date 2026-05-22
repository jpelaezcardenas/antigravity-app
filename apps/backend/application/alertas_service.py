"""
AlertasService — Evaluates tax threshold alerts.

Note: This is an alternative implementation to CentinelaService.
CentinelaService is the primary one used by the API endpoints.
This module remains for reference and potential future use.
"""

from typing import List
from datetime import date
from domain.alerta import AlertaTributaria
from core.constants import UMBRAL_RENTA_COP, UMBRAL_IVA_COP


class AlertasService:
    def __init__(self, trans_repo=None, user_repo=None):
        self.trans_repo = trans_repo
        self.user_repo = user_repo

    def obtener_alertas_umbrales(self, user_id: str) -> List[AlertaTributaria]:
        """Calculate threshold alerts for a given user."""
        today = date.today()
        start_of_year = date(today.year, 1, 1)
        
        transacciones = self.trans_repo.get_by_date_range(user_id, start_of_year, today)
        ingresos_anuales = sum(t.monto for t in transacciones if t.tipo == "ingreso")
        
        alertas = []
        
        # Alerta Renta
        uso_renta = ingresos_anuales / UMBRAL_RENTA_COP
        alertas.append(self._crear_alerta_umbral(
            "Renta", uso_renta, ingresos_anuales, UMBRAL_RENTA_COP
        ))
        
        # Alerta IVA
        uso_iva = ingresos_anuales / UMBRAL_IVA_COP
        alertas.append(self._crear_alerta_umbral(
            "IVA", uso_iva, ingresos_anuales, UMBRAL_IVA_COP
        ))
        
        return alertas

    def _crear_alerta_umbral(
        self, impuesto: str, uso: float, actual: float, umbral: float
    ) -> AlertaTributaria:
        if uso >= 0.9:
            severidad = "roja"
        elif uso >= 0.7:
            severidad = "amarilla"
        else:
            severidad = "verde"
            
        return AlertaTributaria(
            nombre=impuesto,
            porcentaje=round(uso * 100, 2),
            valor_actual=actual,
            umbral=umbral,
            severidad=severidad,
        )
