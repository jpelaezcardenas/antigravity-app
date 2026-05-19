from infrastructure.repositories.transaccion_repo import TransaccionRepository
from infrastructure.repositories.usuario_repo import UsuarioRepository
from core.constants import UMBRAL_RENTA_COP, UMBRAL_IVA_COP
from domain.alerta import AlertaTributaria
import logging

logger = logging.getLogger(__name__)

class CentinelaService:
    def __init__(self):
        self.transaccion_repo = TransaccionRepository()
        self.usuario_repo = UsuarioRepository()

    async def evaluar_umbrales(self, usuario_id: str):
        user = await self.usuario_repo.get_by_id(usuario_id)
        if not user:
            return []

        # Obtenemos todas las transacciones del año actual (simplificado a todas por ahora)
        transactions = await self.transaccion_repo.get_all_by_usuario(usuario_id)
        
        ingresos_anuales = sum(t["monto"] for t in transactions if t["tipo"] == "ingreso")
        
        alertas = []
        
        # Evaluación Renta
        porcentaje_renta = (ingresos_anuales / UMBRAL_RENTA_COP) * 100
        alertas.append(self._generar_alerta_tributaria(
            "Umbral Declaración Renta",
            porcentaje_renta,
            ingresos_anuales,
            UMBRAL_RENTA_COP
        ))
        
        # Evaluación IVA
        porcentaje_iva = (ingresos_anuales / UMBRAL_IVA_COP) * 100
        alertas.append(self._generar_alerta_tributaria(
            "Umbral Responsable IVA",
            porcentaje_iva,
            ingresos_anuales,
            UMBRAL_IVA_COP
        ))
        
        return alertas

    def _generar_alerta_tributaria(self, nombre, porcentaje, actual, umbral):
        severidad = "verde"
        if porcentaje > 90:
            severidad = "roja"
        elif porcentaje > 70:
            severidad = "amarilla"
            
        # Estimación simple de días basada en promedio (ficticio para la demo)
        dias_estimados = None
        if porcentaje < 100 and actual > 0:
            promedio_diario = actual / 30 # Asumiendo 30 días de datos
            if promedio_diario > 0:
                restante = umbral - actual
                dias_estimados = int(restante / promedio_diario)

        return AlertaTributaria(
            nombre=nombre,
            porcentaje=round(porcentaje, 2),
            valor_actual=actual,
            umbral=umbral,
            severidad=severidad,
            dias_estimados=dias_estimados
        )
        
