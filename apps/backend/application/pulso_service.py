from datetime import date
from typing import List
from domain.transaccion import PulsoDiario, Transaccion
from infrastructure.repositories.transaccion_repository import TransaccionRepository
from infrastructure.repositories.usuario_repository import UsuarioRepository

class PulsoService:
    def __init__(
        self, 
        trans_repo: TransaccionRepository = TransaccionRepository(),
        user_repo: UsuarioRepository = UsuarioRepository()
    ):
        self.trans_repo = trans_repo
        self.user_repo = user_repo

    def calcular_pulso_diario(self, user_id: str, fecha: date = date.today()) -> PulsoDiario:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            # Fallback para demo
            porcentaje_renta = 0.35
            porcentaje_iva = 0.19
        else:
            porcentaje_renta = user.porcentaje_renta
            porcentaje_iva = user.porcentaje_iva

        transacciones = self.trans_repo.get_by_date_range(user_id, fecha, fecha)
        
        ingresos = sum(t.monto for t in transacciones if t.tipo == "ingreso")
        gastos = sum(t.monto for t in transacciones if t.tipo == "gasto")
        
        margen = ingresos - gastos
        
        # Lógica de GPS Financiero: Cuánto es realmente tuyo
        # Asumiendo que los ingresos incluyen IVA (brutos) y gastos incluyen IVA
        # Esto es una simplificación para el MVP
        provision_iva = ingresos * (porcentaje_iva / (1 + porcentaje_iva))
        provision_renta = (ingresos - gastos) * porcentaje_renta if (ingresos - gastos) > 0 else 0
        
        provision_total = provision_iva + provision_renta
        dinero_tuyo = margen - provision_total

        advertencias = []
        if dinero_tuyo < 0:
            advertencias.append("Alerta: Estás gastando dinero que le pertenece a la DIAN.")
        
        return PulsoDiario(
            fecha=fecha,
            ingresos_hoy=ingresos,
            gastos_hoy=gastos,
            margen_hoy=margen,
            provision_dian=provision_total,
            dinero_tuyo_hoy=dinero_tuyo,
            advertencias=advertencias
        )
