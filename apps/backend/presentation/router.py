from fastapi import APIRouter
from presentation.auth_endpoints import router as auth_router
from presentation.pulso_endpoints import router as pulso_router
from presentation.centinela_endpoints import router as centinela_router
from presentation.cobro_endpoints import router as cobro_router
from presentation.agents_endpoints import router as agents_router
from presentation.taty_endpoints import router as taty_router
from presentation.telegram_endpoints import router as telegram_router
from presentation.kb_endpoints import router as kb_router
from presentation.radar_endpoints import router as radar_router
from presentation.wizard_endpoints import router as wizard_router
from presentation.social_ops_endpoints import router as social_ops_router
from presentation.meta_endpoints import router as meta_router
from presentation.tiktok_endpoints import router as tiktok_router
from presentation.linkedin_endpoints import router as linkedin_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(pulso_router, prefix="/pulso", tags=["pulso"])
api_router.include_router(centinela_router, prefix="/centinela", tags=["centinela"])
api_router.include_router(cobro_router, prefix="/cobro", tags=["cobro"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(taty_router, prefix="/agents", tags=["taty"])
api_router.include_router(telegram_router, prefix="/channels", tags=["telegram"])
api_router.include_router(social_ops_router, prefix="/social-ops", tags=["social-ops"])
api_router.include_router(meta_router, prefix="/channels/meta", tags=["meta"])
api_router.include_router(tiktok_router, prefix="/channels/tiktok", tags=["tiktok"])
api_router.include_router(linkedin_router, prefix="/channels/linkedin", tags=["linkedin"])
api_router.include_router(kb_router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(radar_router, prefix="/radar", tags=["radar"])
api_router.include_router(wizard_router, prefix="/wizard", tags=["wizard"])
