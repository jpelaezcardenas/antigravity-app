from fastapi import APIRouter
from presentation.auth_router import router as auth_router
from presentation.pulso_router import router as pulso_router
from presentation.alertas_router import router as alertas_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(pulso_router, prefix="/pulso", tags=["Pulso Diario"])
api_router.include_router(alertas_router, prefix="/alertas", tags=["Alertas Fiscales"])
