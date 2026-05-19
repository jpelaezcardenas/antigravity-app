from infrastructure.repositories.factura_repo import FacturaRepository
from domain.factura import AlertaCobro
from datetime import date
import logging

logger = logging.getLogger(__name__)

class CobroService:
    def __init__(self):
        self.factura_repo = FacturaRepository()

    async def monitorear_cartera_vencida(self, usuario_id: str):
        facturas = await self.factura_repo.get_vencidas_by_usuario(usuario_id)
        hoy = date.today()
        
        alertas = []
        for f in facturas:
            vencimiento = date.fromisoformat(f["fecha_vencimiento"])
            dias_vencidos = (hoy - vencimiento).days
            
            if dias_vencidos > 0:
                urgencia = "bajo"
                if dias_vencidos > 45:
                    urgencia = "alto"
                elif dias_vencidos > 15:
                    urgencia = "medio"
                    
                alertas.append(AlertaCobro(
                    factura_id=str(f["id"]),
                    cliente=f["cliente"],
                    dias_vencidos=dias_vencidos,
                    monto=float(f["monto"]),
                    nivel_urgencia=urgencia
                ))
        
        return alertas

    async def registrar_intento_cobro(self, usuario_id: str, data: dict):
        # Registrar el evento
        evento_data = {
            "usuario_id": usuario_id,
            "factura_id": data["factura_id"],
            "tipo_evento": data["tipo_evento"],
            "resultado": data["resultado"],
            "monto_comprometido": data.get("monto_comprometido"),
            "fecha_pago_comprometida": data.get("fecha_pago_comprometida")
        }
        await self.factura_repo.register_evento_cobro(evento_data)
        
        # Incrementar contador en la factura
        await self.factura_repo.increment_intentos_cobro(data["factura_id"])
        
        return {"status": "success", "message": "Intento de cobro registrado"}

    async def generar_carta_cobro(self, usuario_id: str, factura_id: str, tipo: str):
        factura = await self.factura_repo.get_by_id(factura_id)
        if not factura:
            return "Factura no encontrada"
            
        # Generación de plantilla según el tipo
        plantillas = {
            "amigable": f"Estimado {factura['cliente']}, le recordamos amablemente que la factura {factura['numero_factura']} por ${factura['monto']} se encuentra vencida...",
            "formal": f"Cordial saludo. Por medio de la presente, solicitamos el pago de la factura {factura['numero_factura']} con fecha de vencimiento {factura['fecha_vencimiento']}...",
            "urgente": f"AVISO DE COBRO: La factura {factura['numero_factura']} presenta un retraso crítico. Por favor regularice su situación de inmediato..."
        }
        
        return plantillas.get(tipo, plantillas["formal"])
