from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Contexia API"
    }
