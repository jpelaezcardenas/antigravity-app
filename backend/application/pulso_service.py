from infrastructure.repositories.transaccion_repo import TransaccionRepository
from infrastructure.repositories.usuario_repo import UsuarioRepository
from domain.transaccion import PulsoDiario
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

class PulsoService:
    def __init__(self):
        self.transaccion_repo = TransaccionRepository()
        self.usuario_repo = UsuarioRepository()

    async def calcular_pulso_diario(self, usuario_id: str, fecha: date = None):
        if not fecha:
            fecha = date.today()
            
        user = await self.usuario_repo.get_by_id(usuario_id)
        if not user:
            return None

        # Obtenemos transacciones de los últimos 30 días para contexto, pero nos enfocamos en el día
        # O según la lógica de Contexia: "dinero tuyo hoy"
        # Traeremos todas las transacciones del mes actual para el cálculo
        start_date = fecha.replace(day=1)
        end_date = fecha
        
        transactions = await self.transaccion_repo.get_by_usuario_and_date(usuario_id, start_date, end_date)
        
        ingresos = sum(t["monto"] for t in transactions if t["tipo"] == "ingreso")
        gastos = sum(t["monto"] for t in transactions if t["tipo"] == "gasto")
        margen = ingresos - gastos
        
        # Provisión DIAN basada en los porcentajes del usuario
        provision_renta = ingresos * user.get("porcentaje_renta", 0.35)
        provision_iva = (ingresos - gastos) * user.get("porcentaje_iva", 0.19)
        if provision_iva < 0: provision_iva = 0
        
        total_provision = provision_renta + provision_iva
        dinero_tuyo = margen - total_provision
        
        advertencias = []
        # Detectar falta de sincronización (ej: si no hay transacciones hoy)
        transacciones_hoy = [t for t in transactions if t["fecha"] == fecha.isoformat()]
        if not transacciones_hoy:
            advertencias.append("No se detectan transacciones sincronizadas hoy")
            
        # Brechas anormales (ej: si gastos > ingresos)
        if gastos > ingresos:
            advertencias.append("Alerta: Los gastos superan los ingresos este mes")

        return PulsoDiario(
            fecha=fecha,
            ingresos=ingresos,
            gastos=gastos,
            margen=margen,
            provision_dian=total_provision,
            dinero_tuyo_hoy=dinero_tuyo,
            advertencias=advertencias
        )
