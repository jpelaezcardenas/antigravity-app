from fastapi import APIRouter, Depends
from domain.usuario import LoginRequest, Token
from application.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(request: LoginRequest, service: AuthService = Depends(AuthService)):
    return service.login(request)
