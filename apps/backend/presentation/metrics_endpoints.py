from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.deps import get_current_user
from core.tenant_context import resolve_request_tenant_scope
from models.metrics import (
    AutoApprovalMetricsResponse,
    CSVIngestionMetricsResponse,
    QueueHealthResponse,
    SnapshotComputeResponse,
    VendorEntry,
)
from models.user import User
from services.metrics_service import (
    compute_and_upsert_snapshot,
    get_auto_approval_metrics,
    get_csv_ingestion_metrics,
    get_queue_health,
    get_top_vendors,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _tenant(user: Annotated[User, Depends(get_current_user)]) -> str:
    scope = resolve_request_tenant_scope(user, None)
    return str(scope.tenant_id)


@router.get("/auto-approval/last-7-days", response_model=AutoApprovalMetricsResponse)
async def auto_approval_last_7_days(
    tenant_id: str = Depends(_tenant),
    days: Annotated[int, Query(ge=1, le=90)] = 7,
):
    return get_auto_approval_metrics(tenant_id, days)


@router.get("/csv-ingestion/last-7-days", response_model=CSVIngestionMetricsResponse)
async def csv_ingestion_last_7_days(
    tenant_id: str = Depends(_tenant),
    days: Annotated[int, Query(ge=1, le=90)] = 7,
):
    return get_csv_ingestion_metrics(tenant_id, days)


@router.get("/queue-health", response_model=QueueHealthResponse)
async def queue_health(tenant_id: str = Depends(_tenant)):
    return get_queue_health(tenant_id)


@router.get("/top-vendors", response_model=list[VendorEntry])
async def top_vendors(
    tenant_id: str = Depends(_tenant),
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return get_top_vendors(tenant_id, limit)


@router.post("/snapshot/compute", response_model=SnapshotComputeResponse)
async def compute_snapshot(
    tenant_id: str = Depends(_tenant),
    date: Annotated[str | None, Query()] = None,
):
    return compute_and_upsert_snapshot(tenant_id, date)
