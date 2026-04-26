from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from presentation.router import api_router
from presentation.health_endpoints import router as health_router
import uvicorn

app = FastAPI(
    title="Contexia API",
    description="Backend para la plataforma de Inteligencia Financiera Contexia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS
origins = [
    "http://localhost:5173",
    "https://contexia.online",
    "https://*.contexia.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
