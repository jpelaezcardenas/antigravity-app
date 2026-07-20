"""Sell Machine creative-swarm + Hermes/Manus execution bridge endpoints
(sell-machine-creative-swarm Change E, hermes-manus-execution-bridge Change F).

Mounted at /api/v1/sell-machine behind the SELL_MACHINE_CANONICAL feature flag (see
presentation/router.py). Campaign-package approve/reject reuse the existing, unmodified
/api/v1/approval-queue/approve and /reject endpoints — no new approval routes here.

The operator-task routes (Change F) reuse this same file/flag rather than a new module, since
they share the router prefix and the flag is already live in production (design.md Decision 3).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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
)

router = APIRouter(tags=["sell-machine"])


class GenerateHooksRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)


@router.post("/hooks/generate")
def generate_hooks_endpoint(payload: GenerateHooksRequest):
    hooks = generate_hooks(count=payload.count)
    return {"hooks": hooks}


class EvaluateHooksRequest(BaseModel):
    hooks: List[Dict[str, Any]]


@router.post("/hooks/evaluate")
def evaluate_hooks_endpoint(payload: EvaluateHooksRequest):
    survivors = evaluate_hooks(payload.hooks)
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
async def create_campaign_endpoint(payload: CreateCampaignRequest):
    decision = await create_campaign_package(
        hooks=payload.hooks,
        brief=payload.brief,
        target_segment=payload.target_segment,
        budget=payload.budget,
    )
    return _to_dict(decision)


@router.get("/campaigns")
async def list_campaigns_endpoint(status: Optional[str] = Query(default=None)):
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


@router.get("/tasks/pending")
def list_pending_tasks_endpoint():
    return list_pending_tasks()


class CreateTaskRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)


@router.post("/tasks")
def create_task_endpoint(payload: CreateTaskRequest):
    success, row, error = create_task(task_type=payload.task_type, payload=payload.payload)
    if not success:
        _raise_for_error(error)
    return row


@router.post("/campaigns/{decision_id}/dispatch")
async def dispatch_campaign_endpoint(decision_id: str):
    success, row, error = await dispatch_campaign_package(decision_id)
    if not success:
        _raise_for_error(error)
    return row


class TaskStatusRequest(BaseModel):
    status: str


@router.post("/tasks/{task_id}/status")
def task_status_endpoint(task_id: str, payload: TaskStatusRequest):
    if payload.status != "dispatched":
        raise HTTPException(status_code=400, detail="only the 'dispatched' transition is supported here")
    success, row, error = mark_dispatched(task_id)
    if not success:
        _raise_for_error(error)
    return row


class TaskResultRequest(BaseModel):
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)


@router.post("/tasks/{task_id}/result")
def task_result_endpoint(task_id: str, payload: TaskResultRequest):
    success, row, error = report_result(task_id, status=payload.status, result=payload.result)
    if not success:
        _raise_for_error(error)
    return row
