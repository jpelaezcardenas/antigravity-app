from fastapi import APIRouter, Depends, HTTPException, status
from domain.usuario import LoginRequest, TokenResponse
from application.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    POST /api/v1/auth/login
    Body: { email, password }
    Response: { token, usuario_id, nombre_empresa }
    """
    try:
        result = await auth_service.login(credentials.email, credentials.password)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la autenticación: {str(e)}"
        )
