from typing import List
from domain.alerta import AlertaTributaria
from domain.transaccion import Transaccion
from infrastructure.repositories.transaccion_repository import TransaccionRepository
from infrastructure.repositories.usuario_repository import UsuarioRepository
from core.constants import UMBRAL_RENTA_COP, UMBRAL_IVA_COP

class AlertasService:
    def __init__(
        self, 
        trans_repo: TransaccionRepository = TransaccionRepository(),
        user_repo: UsuarioRepository = UsuarioRepository()
    ):
        self.trans_repo = trans_repo
        self.user_repo = user_repo

    def obtener_alertas_umbrales(self, user_id: str) -> List[AlertaTributaria]:
        # Obtener ingresos acumulados del año (simplificado)
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

    def _crear_alerta_umbral(self, impuesto: str, uso: float, actual: float, umbral: float) -> AlertaTributaria:
        if uso >= 0.9:
            severidad = "roja"
            mensaje = f"¡Peligro! Has superado el 90% del umbral de {impuesto}. Debes actuar ya."
        elif uso >= 0.7:
            severidad = "amarilla"
            mensaje = f"Atención: Has superado el 70% del umbral de {impuesto}. Planea tu transición."
        else:
            severidad = "verde"
            mensaje = f"Todo bajo control con {impuesto}. Estás al {uso:.1%} del umbral."
            
        return AlertaTributaria(
            impuesto=impuesto,
            porcentaje_uso=uso,
            valor_actual=actual,
            umbral=umbral,
            severidad=severidad,
            mensaje=mensaje
        )

from datetime import date # Import faltante
