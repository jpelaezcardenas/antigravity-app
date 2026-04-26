from infrastructure.supabase_client import supabase_client
from datetime import date
import logging

logger = logging.getLogger(__name__)

class TransaccionRepository:
    def __init__(self):
        self.client = supabase_client

    async def get_by_usuario_and_date(self, usuario_id: str, start_date: date, end_date: date):
        try:
            response = self.client.table("transacciones") \
                .select("*") \
                .eq("usuario_id", usuario_id) \
                .gte("fecha", start_date.isoformat()) \
                .lte("fecha", end_date.isoformat()) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []

    async def get_all_by_usuario(self, usuario_id: str):
        try:
            response = self.client.table("transacciones") \
                .select("*") \
                .eq("usuario_id", usuario_id) \
                .order("fecha", desc=True) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching all transactions: {e}")
            return []
