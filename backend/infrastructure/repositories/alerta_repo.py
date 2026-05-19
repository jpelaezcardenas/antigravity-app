from infrastructure.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)

class AlertaRepository:
    def __init__(self):
        self.client = supabase_client

    async def get_active_by_usuario(self, usuario_id: str):
        try:
            response = self.client.table("alertas_fiscales") \
                .select("*") \
                .eq("usuario_id", usuario_id) \
                .eq("activa", True) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching active alerts: {e}")
            return []
            
    async def create_alerta(self, alerta_data: dict):
        try:
            response = self.client.table("alertas_fiscales").insert(alerta_data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
            
    async def deactivate_alerts_by_type(self, usuario_id: str, tipo: str):
        try:
            self.client.table("alertas_fiscales") \
                .update({"activa": False}) \
                .eq("usuario_id", usuario_id) \
                .eq("tipo", tipo) \
                .execute()
        except Exception as e:
            logger.error(f"Error deactivating alerts: {e}")
