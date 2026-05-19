from infrastructure.repositories.usuario_repo import UsuarioRepository
from core.security import verify_password, create_access_token
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.usuario_repo = UsuarioRepository()

    async def login(self, email: str, password: str):
        # Manejo de usuarios de prueba para demo
        # En producción se usaría el hash real de la DB
        # Pero el plan dice que el password es 'demo' para los 3 usuarios de prueba
        
        user_data = await self.usuario_repo.get_by_email(email)
        
        if not user_data:
            logger.warning(f"Login failed: User {email} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        # Para la demo, si el password_hash en la DB es un placeholder, aceptamos 'demo'
        is_valid = False
        if user_data["password_hash"].startswith("$2b$12$placeholder"):
            if password == "demo":
                is_valid = True
        else:
            is_valid = verify_password(password, user_data["password_hash"])

        if not is_valid:
            logger.warning(f"Login failed: Invalid password for {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        token = create_access_token(data={"sub": user_data["id"], "email": user_data["email"]})
        
        return {
            "token": token,
            "usuario_id": str(user_data["id"]),
            "nombre_empresa": user_data["nombre_empresa"]
        }
