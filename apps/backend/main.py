from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from presentation.router import api_router
from presentation.health_endpoints import router as health_router
from core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from config import settings
from middleware_config import apply_middleware
import uvicorn
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("contexia-api")

app = FastAPI(
    title="Contexia API",
    description="Backend para la plataforma de Inteligencia Financiera Contexia",
    version="1.0.0",
    # Disable API docs in production to prevent endpoint discovery
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# --- Middleware Stack (order matters: last added = first executed) ---

# 1. CORS — hardcoded to ensure all local dev ports are allowed
cors_origins = [
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

# Manejo de errores global — never expose internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


# Incluir routers
api_router.include_router(health_router)

# Secrets router — imported defensively so a failure never crashes app startup
try:
    from api.endpoints.secrets_endpoints import router as secrets_router
    api_router.include_router(secrets_router)
    logger.info("Secrets router registered successfully")
except Exception as e:
    logger.error(f"Failed to include secrets_router: {e}")

app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
