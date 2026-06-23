"""
Prometheus Metrics Endpoints
Exposes /metrics endpoint for Grafana scraping
"""

from fastapi import APIRouter, Response
from prometheus_metrics import get_metrics

router = APIRouter(tags=["monitoring"])


@router.get("/metrics", response_class=Response)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    Scrape this endpoint from Grafana to collect metrics

    Exposed metrics:
    - agent_latency_seconds: Agent response time
    - agent_errors_total: Agent error count
    - websocket_connections_active: Active WebSocket connections
    - cache_hit_rate: Cache hit percentage
    - request_duration_seconds: HTTP request latency
    """
    return Response(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
