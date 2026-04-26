from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre_empresa: str
    nit: Optional[str] = None
    plan: str = "starter"
    porcentaje_renta: float = 0.35
    porcentaje_iva: float = 0.19
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    token: str
    usuario_id: str
    nombre_empresa: str
