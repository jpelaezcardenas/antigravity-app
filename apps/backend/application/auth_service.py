from infrastructure.repositories.usuario_repo import UsuarioRepository
from core.security import verify_password, create_access_token
from config import settings
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

        # Check demo users first (for MVP testing), gated by DEMO_AUTH_ENABLED.
        if settings.DEMO_AUTH_ENABLED and email in DEMO_USERS:
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

        # Verify the password against the stored bcrypt hash. Malformed or legacy
        # placeholder hashes are treated as invalid credentials, never bypassed.
        is_valid = False
        try:
            is_valid = verify_password(password, user_data["password_hash"])
        except Exception as exc:
            logger.warning(f"Password verification error for {email}: {exc}")

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
