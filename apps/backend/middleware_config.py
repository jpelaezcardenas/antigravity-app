"""
DAY 6: FastAPI Middleware Configuration
Rate limiting, CORS, error handling, and request logging
Apply these to your main FastAPI app for production hardening
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time
import os
from datetime import datetime

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("contexia-api")

# ============================================================================
# RATE LIMITER
# ============================================================================

limiter = Limiter(key_func=get_remote_address)

# ============================================================================
# ALLOWED ORIGINS
# ============================================================================

# Load from .env or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

print(f"[INFO] CORS enabled for origins: {ALLOWED_ORIGINS}")

# ============================================================================
# APPLY MIDDLEWARE TO APP
# ============================================================================

def apply_middleware(app: FastAPI):
    """
    Apply all middleware to FastAPI app
    Call this in your main.py:
        from middleware_config import apply_middleware
        apply_middleware(app)
    """

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware applied")

    # 2. Rate Limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    logger.info("Rate limiter applied (30 requests/minute per IP)")

    # 3. Request/Response Logging Middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests with timing"""
        request_id = f"{datetime.now().timestamp()}"
        start_time = time.time()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} | "
            f"Client: {get_remote_address(request)}"
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] EXCEPTION | {str(e)} | Time: {process_time:.3f}s"
            )
            raise

    logger.info("Request logging middleware applied")

    # 4. Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Standardized error responses"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if os.getenv("DEBUG") == "True" else "Please contact support",
                "timestamp": datetime.now().isoformat()
            }
        )

    logger.info("Global exception handler applied")

    return app

# ============================================================================
# RATE LIMIT EXCEPTION HANDLER
# ============================================================================

async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": "Rate limit exceeded: 30 requests per minute",
            "retry_after": 60
        }
    )

# ============================================================================
# EXAMPLE: HOW TO USE IN main.py
# ============================================================================

EXAMPLE_MAIN_PY = """
# In your main.py or app.py:

from fastapi import FastAPI
from middleware_config import apply_middleware, limiter
from presentation.agents_endpoints import router as agents_router

app = FastAPI(title="Contexia Platform - DAY 6")

# Apply middleware FIRST
apply_middleware(app)

# Include routers
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])

# Apply rate limiter to specific endpoint (optional):
@app.get("/api/v1/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

# ============================================================================
# RATE LIMITING STRATEGIES
# ============================================================================

RATE_LIMIT_STRATEGIES = {
    "public_endpoints": "100/minute",          # Public health checks
    "agent_endpoints": "30/minute",             # Agent API (computation-heavy)
    "pulso_endpoints": "20/minute",             # KPI dashboard
    "centinela_endpoints": "30/minute",         # Risk alerts
    "taty_endpoints": "50/minute",              # Q&A (can be more frequent)
    "admin_endpoints": "1000/minute",           # Internal/admin endpoints
}

"""
# Apply per-endpoint rate limits:

@app.post("/api/v1/agents/orchestrator/full-pipeline")
@limiter.limit("30/minute")
async def full_pipeline(request: Request, body: dict):
    ...

@app.post("/api/v1/pulso/today")
@limiter.limit("20/minute")
async def pulso_today(request: Request, company_id: str):
    ...

@app.post("/api/v1/centinela/check-risks")
@limiter.limit("30/minute")
async def centinela_check(request: Request, company_id: str):
    ...

@app.post("/api/v1/taty/ask")
@limiter.limit("50/minute")
async def taty_ask(request: Request, body: dict):
    ...
"""

# ============================================================================
# DEPENDENCY: INSTALL slowapi
# ============================================================================

INSTALLATION = """
pip install slowapi
"""

# DEBUG: Removed print(EXAMPLE_MAIN_PY) — was causing reloader confusion on startup
