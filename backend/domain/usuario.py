from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Usuario(BaseModel):
    id: str
    email: EmailStr
    nombre_empresa: str
    nit: str
    plan: str  # "starter" | "growth" | "enterprise"
    porcentaje_renta: float = 0.35
    porcentaje_iva: float = 0.19
    activo: bool = True
    created_at: datetime

class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str
    nombre_empresa: str
    nit: str
    plan: str = "starter"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    usuario_id: str
    nombre_empresa: str
