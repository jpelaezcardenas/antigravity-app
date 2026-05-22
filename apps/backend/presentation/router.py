from fastapi import APIRouter
from presentation.auth_endpoints import router as auth_router
from presentation.pulso_endpoints import router as pulso_router
from presentation.centinela_endpoints import router as centinela_router
from presentation.cobro_endpoints import router as cobro_router
from presentation.llm_endpoints import router as llm_router
from presentation.social_content_endpoints import router as social_content_router
from presentation.content_management_endpoints import router as content_management_router
from presentation.agents_endpoints import router as agents_router
from routes.workflows import router as workflows_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(pulso_router, prefix="/pulso", tags=["pulso"])
api_router.include_router(centinela_router, prefix="/centinela", tags=["centinela"])
api_router.include_router(cobro_router, prefix="/cobro", tags=["cobro"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])
api_router.include_router(social_content_router, prefix="/social-content-ops", tags=["social-content-ops"])
api_router.include_router(content_management_router, prefix="/social-content-ops/content", tags=["content-management"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(workflows_router, tags=["workflows"])
