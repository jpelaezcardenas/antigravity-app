from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from presentation.router import api_router
from presentation.health_endpoints import router as health_router
from core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from config import settings
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

# 1. CORS — uses centralized config from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# 2. Security Headers (XSS, Clickjacking, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request Logging
app.add_middleware(RequestLoggingMiddleware)


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
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
