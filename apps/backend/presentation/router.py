from fastapi import APIRouter
from config import settings
from presentation.auth_endpoints import router as auth_router
from presentation.pulso_endpoints import router as pulso_router
from presentation.centinela_endpoints import router as centinela_router
from presentation.centinela_agents_endpoints import router as centinela_agents_router
from presentation.cobro_endpoints import router as cobro_router
from presentation.agents_endpoints import router as agents_router
from presentation.taty_endpoints import router as taty_router
from presentation.telegram_endpoints import router as telegram_router
from presentation.kb_endpoints import router as kb_router
from presentation.radar_endpoints import router as radar_router
from presentation.wizard_endpoints import router as wizard_router
from presentation.social_ops_endpoints import router as social_ops_router
from presentation.meta_endpoints import router as meta_router
from presentation.whatsapp_endpoints import router as whatsapp_router
from presentation.tiktok_endpoints import router as tiktok_router
from presentation.linkedin_endpoints import router as linkedin_router
from presentation.financials_endpoints import router as financials_router
from presentation.critic_endpoints import router as critic_router
from presentation.approval_queue_endpoints import router as approval_queue_router
from presentation.shadow_gl_endpoints import router as shadow_gl_router
from presentation.pulso_diario_endpoints import router as pulso_diario_router
from presentation.auditoria_sombra_endpoints import router as auditoria_sombra_router
from presentation.crm_endpoints import router as crm_router
from presentation.sell_machine_endpoints import router as sell_machine_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(pulso_router, prefix="/pulso", tags=["pulso"])
api_router.include_router(centinela_router, prefix="/centinela", tags=["centinela"])
api_router.include_router(centinela_agents_router, prefix="/agents/centinela", tags=["centinela-agents"])
api_router.include_router(cobro_router, prefix="/cobro", tags=["cobro"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
# taty_router intentionally shares the /agents prefix. Its paths (/agents/ask,
# /agents/health) do not collide with agents_router's paths (/agents/social/...,
# etc.), so both can be mounted at the same prefix. (The deprecated
# /agents/taty/ask wrapper route was deleted — taty-per-tenant-profiles, task 5.)
api_router.include_router(taty_router, prefix="/agents", tags=["taty"])
api_router.include_router(telegram_router, prefix="/channels", tags=["telegram"])

# Social Ops canonical endpoints — feature flag gated (default off, n8n still routes)
if settings.SOCIAL_OPS_CANONICAL:
    api_router.include_router(social_ops_router, prefix="/social-ops", tags=["social-ops"])
api_router.include_router(meta_router, prefix="/channels/meta", tags=["meta"])
api_router.include_router(tiktok_router, prefix="/channels/tiktok", tags=["tiktok"])
api_router.include_router(linkedin_router, prefix="/channels/linkedin", tags=["linkedin"])
api_router.include_router(kb_router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(radar_router, prefix="/agents/radar-predictivo", tags=["radar"])
api_router.include_router(wizard_router, prefix="/wizard", tags=["wizard"])
api_router.include_router(financials_router, prefix="/financials", tags=["financials"])
api_router.include_router(critic_router, prefix="/critic", tags=["critic"])
api_router.include_router(approval_queue_router, prefix="/approval-queue", tags=["approval-queue"])
api_router.include_router(shadow_gl_router, prefix="/shadow-gl", tags=["shadow-gl"])
api_router.include_router(pulso_diario_router, prefix="/agents/pulso-diario", tags=["pulso-diario"])
api_router.include_router(auditoria_sombra_router, prefix="/agents/auditoria-sombra", tags=["auditoria-sombra"])

# CRM B2B retainers cockpit — feature flag gated (default off, flip after Stage 11 smoke-test)
if settings.CRM_CANONICAL:
    api_router.include_router(crm_router, prefix="/crm", tags=["crm"])

# Sell Machine creative swarm — feature flag gated (default off, flip after Stage 11 smoke-test)
if settings.SELL_MACHINE_CANONICAL:
    api_router.include_router(sell_machine_router, prefix="/sell-machine", tags=["sell-machine"])

# Taty WhatsApp channel — mounted unconditionally (taty-channel-consolidation). This is the
# production ingress from Meta via vercel.json's /api/v1/:path* rewrite; a feature flag here would
# only risk silently dropping live customer messages. Authenticity is enforced by
# X-Hub-Signature-256 verification inside the handler.
api_router.include_router(whatsapp_router, prefix="/channels/whatsapp", tags=["whatsapp"])
