from core.supabase_client import get_service_supabase
from domain.usuario import Usuario
import logging

logger = logging.getLogger(__name__)

class UsuarioRepository:
    """Reads `usuarios` via the service-role client, matching every other reader of this table
    (identity_resolver.py, crm_service.py). `usuarios` has RLS enabled with no policy — the
    anon client this repo used before could no longer read anything from it."""

    def __init__(self):
        self.client = get_service_supabase()

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
