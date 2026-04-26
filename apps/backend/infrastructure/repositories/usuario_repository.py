from typing import Optional, List
from infrastructure.supabase_client import supabase
from domain.usuario import Usuario, UsuarioCreate
from core.security import hash_password

class UsuarioRepository:
    def get_by_email(self, email: str) -> Optional[Usuario]:
        response = supabase.table("profiles").select("*").eq("email", email).execute()
        if not response.data:
            return None
        return Usuario(**response.data[0])

    def get_by_id(self, user_id: str) -> Optional[Usuario]:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not response.data:
            return None
        return Usuario(**response.data[0])

    def create(self, user: UsuarioCreate) -> Usuario:
        # Nota: En Supabase Auth el usuario se crea vía API de Auth.
        # Aquí manejamos la persistencia en la tabla 'profiles' ligada al auth.uid()
        # Este es un mock de persistencia para la lógica de negocio.
        data = user.model_dump()
        del data["password"] # No guardamos pass en tabla de perfiles
        
        response = supabase.table("profiles").insert(data).execute()
        return Usuario(**response.data[0])
