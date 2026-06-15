from fastapi import APIRouter, Depends
from typing import Dict, Any
from apps.backend.core.secrets_provider import get_provider, SecretsProvider

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.get("/health")
async def secrets_health(provider: SecretsProvider = Depends(get_provider)) -> Dict[str, Any]:
    """
    Health check del provider de secrets activo.

    Response:
    {
      "status": "healthy|unhealthy",
      "provider": "bitwarden-cloud|vaultwarden-selfhosted",
      "latency_ms": <int>,
      "vault_url": "https://...",
      "error": "<msg>" (si status=unhealthy)
    }
    """
    return await provider.health()
