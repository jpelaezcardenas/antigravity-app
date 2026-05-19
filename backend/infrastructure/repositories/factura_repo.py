from infrastructure.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)

class FacturaRepository:
    def __init__(self):
        self.client = supabase_client

    async def get_vencidas_by_usuario(self, usuario_id: str):
        try:
            response = self.client.table("facturas_vencidas") \
                .select("*") \
                .eq("usuario_id", usuario_id) \
                .eq("estado", "no_pagada") \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching overdue invoices: {e}")
            return []

    async def get_by_id(self, factura_id: str):
        try:
            response = self.client.table("facturas_vencidas").select("*").eq("id", factura_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching invoice by id: {e}")
            return None

    async def increment_intentos_cobro(self, factura_id: str):
        try:
            # Primero obtenemos el valor actual
            factura = await self.get_by_id(factura_id)
            if factura:
                new_count = factura.get("intentos_cobro", 0) + 1
                self.client.table("facturas_vencidas") \
                    .update({"intentos_cobro": new_count}) \
                    .eq("id", factura_id) \
                    .execute()
        except Exception as e:
            logger.error(f"Error incrementing collection attempts: {e}")

    async def register_evento_cobro(self, evento_data: dict):
        try:
            response = self.client.table("eventos_cobro").insert(evento_data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error registering collection event: {e}")
            return None
