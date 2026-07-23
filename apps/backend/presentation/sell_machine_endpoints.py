"""Sell Machine creative-swarm + Hermes/Manus execution bridge endpoints
(sell-machine-creative-swarm Change E, hermes-manus-execution-bridge Change F).

Mounted at /api/v1/sell-machine behind the SELL_MACHINE_CANONICAL feature flag (see
presentation/router.py). Campaign-package approve/reject reuse the existing, unmodified
/api/v1/approval-queue/approve and /reject endpoints — no new approval routes here.

The operator-task routes (Change F) reuse this same file/flag rather than a new module, since
they share the router prefix and the flag is already live in production (design.md Decision 3).
"""

from __future__ import annotations

import hmac
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field

from config import settings
from core.deps import get_current_user
from services.agent_operations_logger import agent_operations_logger
from services.copywriter_service import generate_hooks
from services.operator_task_service import (
    create_task,
    dispatch_campaign_package,
    list_pending_tasks,
    mark_dispatched,
    report_result,
)
from services.sell_machine_service import (
    create_campaign_package,
    evaluate_hooks,
    get_telemetry_report,
    list_campaigns,
    run_creative_loop,
)

router = APIRouter(tags=["sell-machine"])


def require_hermes_bridge_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Optional machine-token guard for the 5 operator-task bridge routes
    (hermes-task-queue-tenant-scoping, design.md D5). Reads `settings.HERMES_BRIDGE_TOKEN` at
    call time (not import time) so it stays testable via monkeypatch and picks up env changes
    without a process restart in tests. No-op when unset — preserves today's open behavior."""
    expected = settings.HERMES_BRIDGE_TOKEN
    if not expected:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="invalid bridge token")


class GenerateHooksRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)


@router.post("/hooks/generate")
def generate_hooks_endpoint(
    payload: GenerateHooksRequest, _user: dict = Depends(get_current_user)
):
    hooks = generate_hooks(count=payload.count)
    return {"hooks": hooks}


class EvaluateHooksRequest(BaseModel):
    hooks: List[Dict[str, Any]]


@router.post("/hooks/evaluate")
def evaluate_hooks_endpoint(
    payload: EvaluateHooksRequest, _user: dict = Depends(get_current_user)
):
    survivors = evaluate_hooks(payload.hooks)
    return {"survivors": survivors}


class CreativeLoopRunRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    target_segment: Optional[str] = None


@router.post("/creative-loop/run")
def creative_loop_run_endpoint(payload: CreativeLoopRunRequest):
    """Runs the telemetry-aware creative loop (activate-telemetry-loop) — the only way it runs
    in production, since this repo has no in-backend scheduler; Hermes (local) triggers this on
    its own schedule per the settled architecture (ARCHITECTURE.md decision #1)."""
    survivors = run_creative_loop(
        count=payload.count, target_segment=payload.target_segment, use_telemetry=True
    )
    return {"survivors": survivors}


class CreateCampaignRequest(BaseModel):
    hooks: List[Dict[str, Any]]
    brief: str = Field(..., min_length=1)
    target_segment: str = Field(..., min_length=1)
    budget: Optional[int] = None


def _to_dict(obj: Any) -> Any:
    """Best-effort serialization: ApprovalDecision has .to_dict(); mocks in tests are plain dicts."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj


@router.post("/campaigns")
async def create_campaign_endpoint(
    payload: CreateCampaignRequest, _user: dict = Depends(get_current_user)
):
    decision = await create_campaign_package(
        hooks=payload.hooks,
        brief=payload.brief,
        target_segment=payload.target_segment,
        budget=payload.budget,
    )
    return _to_dict(decision)


@router.get("/campaigns")
async def list_campaigns_endpoint(
    status: Optional[str] = Query(default=None), _user: dict = Depends(get_current_user)
):
    decisions = await list_campaigns(status=status)
    return [_to_dict(d) for d in decisions]


def _raise_for_error(error: str) -> None:
    """Maps a service-layer error string to an HTTP status: 404 if the referenced row wasn't
    found, 409 for an invalid status transition, 400 for everything else (e.g. a rejected
    side-effecting task_type)."""
    if "not found" in error:
        raise HTTPException(status_code=404, detail=error)
    if "is '" in error and "not '" in error:
        raise HTTPException(status_code=409, detail=error)
    raise HTTPException(status_code=400, detail=error)


@router.get("/telemetry/report")
def telemetry_report_endpoint():
    return get_telemetry_report()


@router.get("/tasks/pending", dependencies=[Depends(require_hermes_bridge_token)])
def list_pending_tasks_endpoint(tenant_id: Optional[str] = Query(default=None)):
    return list_pending_tasks(tenant_id=tenant_id)


class CreateTaskRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None


@router.post("/tasks", dependencies=[Depends(require_hermes_bridge_token)])
async def create_task_endpoint(payload: CreateTaskRequest):
    started = time.monotonic()
    success, row, error = create_task(
        task_type=payload.task_type, payload=payload.payload, tenant_id=payload.tenant_id
    )
    if not success:
        _raise_for_error(error)
    duration_ms = int((time.monotonic() - started) * 1000)
    await agent_operations_logger.record(
        tenant_id=row["tenant_id"],
        agent_name="hermes-bridge",
        user_id="machine:hermes",
        operation_type="create_task",
        status="success",
        duration_ms=duration_ms,
        cost=Decimal("0"),
    )
    return row


@router.post("/campaigns/{decision_id}/dispatch", dependencies=[Depends(require_hermes_bridge_token)])
async def dispatch_campaign_endpoint(decision_id: str):
    started = time.monotonic()
    success, row, error = await dispatch_campaign_package(decision_id)
    if not success:
        _raise_for_error(error)
    duration_ms = int((time.monotonic() - started) * 1000)
    await agent_operations_logger.record(
        tenant_id=row["tenant_id"],
        agent_name="hermes-bridge",
        user_id="machine:hermes",
        operation_type="dispatch_campaign",
        status="success",
        duration_ms=duration_ms,
        cost=Decimal("0"),
    )
    return row


class TaskStatusRequest(BaseModel):
    status: str


@router.post("/tasks/{task_id}/status", dependencies=[Depends(require_hermes_bridge_token)])
async def task_status_endpoint(task_id: str, payload: TaskStatusRequest):
    if payload.status != "dispatched":
        raise HTTPException(status_code=400, detail="only the 'dispatched' transition is supported here")
    started = time.monotonic()
    success, row, error = mark_dispatched(task_id)
    if not success:
        _raise_for_error(error)
    duration_ms = int((time.monotonic() - started) * 1000)
    await agent_operations_logger.record(
        tenant_id=row["tenant_id"],
        agent_name="hermes-bridge",
        user_id="machine:hermes",
        operation_type="mark_dispatched",
        status="success",
        duration_ms=duration_ms,
        cost=Decimal("0"),
    )
    return row


class TaskResultRequest(BaseModel):
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)


@router.post("/tasks/{task_id}/result", dependencies=[Depends(require_hermes_bridge_token)])
async def task_result_endpoint(task_id: str, payload: TaskResultRequest):
    started = time.monotonic()
    success, row, error = report_result(task_id, status=payload.status, result=payload.result)
    if not success:
        _raise_for_error(error)
    duration_ms = int((time.monotonic() - started) * 1000)
    await agent_operations_logger.record(
        tenant_id=row["tenant_id"],
        agent_name="hermes-bridge",
        user_id="machine:hermes",
        operation_type="report_result",
        status="success",
        duration_ms=duration_ms,
        cost=Decimal("0"),
    )
    return row
