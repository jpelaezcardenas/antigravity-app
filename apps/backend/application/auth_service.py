from infrastructure.repositories.usuario_repo import UsuarioRepository
from core.security import verify_password, create_access_token
from core.identity_resolver import identity_resolver
from config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


def _resolve_tenant_uuid(sub: str, email: str) -> str | None:
    """Resolve the caller's real tenant UUID for signing into the JWT.

    Fail-open: returns None on any unresolved identity/membership, leaving
    create_access_token's existing string default untouched (see design
    jwt-real-tenant-uuid-claim D3). There is no workspace_id at login time
    (that's what we're creating), so this always falls through to the
    membership-based lookup in IdentityResolver.resolve_tenant_uuid.
    """
    user_uuid = identity_resolver.resolve_user_uuid(sub, email)
    if not user_uuid:
        return None
    return identity_resolver.resolve_tenant_uuid(None, user_uuid)


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
                token_data = {"sub": demo_user["id"], "email": email}
                tenant_uuid = _resolve_tenant_uuid(demo_user["id"], email)
                if tenant_uuid:
                    token_data["tenant_id"] = tenant_uuid
                token = create_access_token(data=token_data)
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

        token_data = {"sub": user_data["id"], "email": user_data["email"]}
        tenant_uuid = _resolve_tenant_uuid(user_data["id"], user_data["email"])
        if tenant_uuid:
            token_data["tenant_id"] = tenant_uuid
        token = create_access_token(data=token_data)

        return {
            "token": token,
            "usuario_id": str(user_data["id"]),
            "nombre_empresa": user_data["nombre_empresa"],
            "email": user_data["email"]
        }
