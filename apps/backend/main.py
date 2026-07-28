from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from presentation.router import api_router
from presentation.health_endpoints import router as health_router
from presentation.metrics_endpoints import router as metrics_router
from core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from core.tenant_middleware import TenantContextMiddleware
from config import settings
from middleware_config import apply_middleware
from prometheus_metrics import add_prometheus_middleware
import uvicorn
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("contexia-api")

# Fail fast on misconfigured production settings (e.g. empty JWT_SECRET) rather
# than starting silently with a forgeable auth secret. Previously defined but
# never called — see openspec/changes/reconcile-railway-antigravity-projects.
settings.validate_production_config()

# Fail fast on Wompi sandbox/production key mismatch or missing production
# credentials — see openspec/changes/wompi-payment-integration.
settings.validate_wompi_config()

app = FastAPI(
    title="Contexia API",
    description="Backend para la plataforma de Inteligencia Financiera Contexia",
    version="1.0.1",  # financials endpoints
    # Disable API docs in production to prevent endpoint discovery
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# --- Middleware Stack (order matters: last added = first executed) ---

# 1. CORS — hardcoded to ensure all local dev ports are allowed
cors_origins = [
    "http://localhost:3001",  # contexia-app dev server (end-user PWA)
    "http://localhost:3002",  # Frontend dev server (Vite)
    "http://localhost:3000",  # Alternative frontend port
    "http://localhost:5173",  # Vite default port
    "http://localhost:5174",  # Alternative Vite port
    "http://localhost:5175",  # Alternative Vite port
    "https://contexia.online",
    "https://www.contexia.online",
    "https://contexia-wizard.vercel.app",
    "https://wizard.contexia.online",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# 2. Security Headers (XSS, Clickjacking, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request Logging
app.add_middleware(RequestLoggingMiddleware)

# 4. DAY 6: Apply production middleware (rate limiting, enhanced logging, etc.)
apply_middleware(app)

# 5. Tenant Context — Extract tenant_id from JWT and inject into request.state
app.add_middleware(TenantContextMiddleware)

# Manejo de errores global — never expose internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


# Add Prometheus middleware for request tracking (Task 3.4)
add_prometheus_middleware(app)

# Incluir routers
print("[STARTUP] Loading routers...", flush=True)
api_router.include_router(health_router)
api_router.include_router(metrics_router, prefix="/monitoring")
print("[STARTUP] Health router loaded", flush=True)
print("[STARTUP] Metrics router loaded - /api/v1/monitoring/metrics", flush=True)

# Secrets router — imported defensively so a failure never crashes app startup
try:
    from api.endpoints.secrets_endpoints import router as secrets_router
    api_router.include_router(secrets_router)
    logger.info("Secrets router registered successfully")
except Exception as e:
    logger.error(f"Failed to include secrets_router: {e}")

# WebSocket router — real-time agent data streaming
print("[STARTUP] Attempting WebSocket router...", flush=True)
try:
    from api.websocket_handler import router as websocket_router
    api_router.include_router(websocket_router)
    print("[STARTUP] WebSocket router SUCCESS", flush=True)
    logger.info("WebSocket router registered successfully")
except Exception as e:
    print(f"[STARTUP] WebSocket router FAILED: {e}", flush=True)
    logger.error(f"Failed to include websocket_router: {e}", exc_info=True)

# Agent endpoints — Centinela, Taty, Social-Ops, Maestro
try:
    from api.agent_endpoints import router as agent_router
    logger.info(f"Agent router imported. Routes count: {len(agent_router.routes)}")
    api_router.include_router(agent_router)
    logger.info(f"Agent endpoints router registered successfully. Total API router routes: {len(api_router.routes)}")
except ImportError as e:
    logger.error(f"Import error in agent_router: {e}", exc_info=True)
except Exception as e:
    logger.error(f"Failed to include agent_router: {e}", exc_info=True)

# Approval Queue endpoints — enqueue, approve, reject drafts
try:
    from presentation.approval_queue_endpoints import router as approval_router
    api_router.include_router(approval_router, prefix="/approval-queue")
    logger.info("Approval queue router registered successfully")
except Exception as e:
    logger.error(f"Failed to include approval_queue_router: {e}", exc_info=True)


# --- Public Privacy Policy page (required by Meta to publish WhatsApp app) ---
PRIVACY_HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Política de Privacidad — Contexia</title>
<style>body{font-family:system-ui,sans-serif;max-width:700px;margin:2rem auto;padding:0 1rem;color:#333}
h1{color:#1a1a2e}h2{margin-top:1.5rem}</style></head><body>
<h1>Política de Privacidad — Contexia</h1>
<p><strong>Última actualización:</strong> julio 2026</p>
<h2>1. Responsable del tratamiento</h2>
<p>Contexia.online — Bogotá, Colombia. Contacto: contexia.marketing@gmail.com</p>
<h2>2. Datos recopilados</h2>
<p>Recopilamos nombre, número de teléfono y mensajes enviados a través de WhatsApp Business API
con el único propósito de brindar asesoría tributaria y contable.</p>
<h2>3. Uso de los datos</h2>
<p>Los datos se usan exclusivamente para: responder consultas tributarias, generar liquidaciones de
impuestos, gestionar pagos a través de pasarelas autorizadas y mejorar la calidad del servicio.</p>
<h2>4. Almacenamiento y seguridad</h2>
<p>Los datos se almacenan en servidores seguros con cifrado en tránsito (TLS) y en reposo.
No compartimos información personal con terceros salvo obligación legal.</p>
<h2>5. Derechos del usuario</h2>
<p>Puedes solicitar acceso, corrección o eliminación de tus datos escribiendo a
contexia.marketing@gmail.com.</p>
<h2>6. Cookies y seguimiento</h2>
<p>Este servicio no utiliza cookies de seguimiento.</p>
</body></html>"""


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy():
    """Public privacy policy page required by Meta for WhatsApp Cloud API app publication."""
    return HTMLResponse(content=PRIVACY_HTML)


app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
