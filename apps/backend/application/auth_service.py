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
        # Permitir login de demo sin requerir BD para testing

        # Demo users hardcoded for MVP testing
        DEMO_USERS = {
            "cliente@demo.co": {
                "id": "usr_cliente_demo",
                "nombre_empresa": "Ferez.co E-commerce",
                "password": "demo"
            },
            "contexia.marketing@gmail.com": {
                "id": "usr_admin_demo",
                "nombre_empresa": "Contexia Admin",
                "password": "Lindafea0712"
            }
        }

        # Check demo users first (for MVP testing)
        if email in DEMO_USERS:
            demo_user = DEMO_USERS[email]
            if password == demo_user["password"]:
                token = create_access_token(data={"sub": demo_user["id"], "email": email})
                logger.info(f"Demo login successful for {email}")
                return {
                    "token": token,
                    "usuario_id": demo_user["id"],
                    "nombre_empresa": demo_user["nombre_empresa"],
                    "email": email
                }
            else:
                logger.warning(f"Login failed: Invalid password for demo user {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )

        # Try database lookup for other users
        user_data = await self.usuario_repo.get_by_email(email)

        if not user_data:
            logger.warning(f"Login failed: User {email} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        # Para la demo, si el password_hash en la DB es un placeholder, aceptamos 'demo' o 'Lindafea0712'
        is_valid = False
        if user_data["password_hash"].startswith("$2b$12$placeholder"):
            if password in ["demo", "Lindafea0712"]:
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
            "nombre_empresa": user_data["nombre_empresa"],
            "email": user_data["email"]
        }
