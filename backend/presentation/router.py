from fastapi import APIRouter
from presentation.auth_endpoints import router as auth_router
from presentation.pulso_endpoints import router as pulso_router
from presentation.centinela_endpoints import router as centinela_router
from presentation.cobro_endpoints import router as cobro_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(pulso_router, prefix="/pulso", tags=["pulso"])
api_router.include_router(centinela_router, prefix="/centinela", tags=["centinela"])
api_router.include_router(cobro_router, prefix="/cobro", tags=["cobro"])
