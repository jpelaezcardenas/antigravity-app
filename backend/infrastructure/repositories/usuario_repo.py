from infrastructure.supabase_client import supabase_client
from domain.usuario import Usuario
import logging

logger = logging.getLogger(__name__)

class UsuarioRepository:
    def __init__(self):
        self.client = supabase_client

    async def get_by_email(self, email: str):
        try:
            response = self.client.table("usuarios").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None

    async def get_by_id(self, user_id: str):
        try:
            response = self.client.table("usuarios").select("*").eq("id", user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching user by id: {e}")
            return None
