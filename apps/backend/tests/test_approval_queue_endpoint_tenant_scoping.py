"""
Tests for the 4 approval-queue endpoints' tenant scoping (approval-queue-tenant-scoping).

Before this change, `presentation/approval_queue_endpoints.py` read a dead
`request.state.tenant_id` (never set by anything, always fell back to the string
`"default-tenant"`) on `POST /enqueue`, and had no tenant scoping at all on
`GET`, `POST /approve`, or `POST /reject`. These tests verify the wiring
described in `openspec/changes/approval-queue-tenant-scoping/design.md`'s
"Endpoint wiring" table:

| Endpoint      | scope is None | scope.all_tenants                  | normal client                          |
|---------------|---------------|-------------------------------------|------------------------------------------|
| GET ""        | empty list    | optional ?tenant_id filter, else -  | forced tenant_id=scope.tenant_id         |
| POST /enqueue | 404           | tenant_id=scope.tenant_id (=CC)     | tenant_id=scope.tenant_id                |
| POST /approve | 404           | tenant_id=None (unrestricted)       | tenant_id=scope.tenant_id                |
| POST /reject  | 404           | tenant_id=None                      | tenant_id=scope.tenant_id                |

Unresolved-scope write rejections return 404, not 403 (agent-endpoints-real-tenant-filtering,
Stage 5) — a 403 would confirm "there is something here you're not allowed to see"; 404
doesn't, matching the anti-enumeration posture already used elsewhere in this repo.

Mirrors `test_financials_endpoint_tenant_scoping.py`'s style: direct coroutine
invocation with fake `user` dicts, no TestClient. Service calls are monkeypatched
at the `ApprovalQueueService` class attribute; tenant scope resolution is
monkeypatched at `presentation.approval_queue_endpoints.resolve_request_tenant_scope`
(the real ladder is already covered by `test_tenant_scope_resolution.py`).
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from fastapi import HTTPException

from core.deps import _STAGING_USER
from core.tenant_context import TenantScope
from models.approval_decisions import ApprovalDecision, ApprovalStatus, VectorizationStatus
from presentation.approval_queue_endpoints import (
    EnqueueRequest,
    JournalLine,
    ApprovalRequest,
    RejectionRequest,
    list_drafts,
    enqueue_for_approval,
    approve_draft,
    reject_draft,
)
from services.approval_queue_service import ApprovalQueueService

CLIENTE_CERO_ID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"
CLIENT_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def run(coro):
    return asyncio.run(coro)


def _client_user() -> dict:
    return {"id": "client-user", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": CLIENT_TENANT_ID}


def _operator_user() -> dict:
    return {"id": "operator-user", "email": "ops@contexia.online", "resolved_user_id": "uuid-op", "resolved_tenant_id": CLIENTE_CERO_ID}


def _unresolved_user() -> dict:
    return {"id": "76680e1f-2943-4235-8501-18b090d59257", "email": "growth@contexia.online", "resolved_user_id": None, "resolved_tenant_id": None}


def _decision(tenant_id: str = CLIENT_TENANT_ID) -> ApprovalDecision:
    return ApprovalDecision(
        id="decision-1",
        draft_id="draft-1",
        draft_type="risk_review",
        status=ApprovalStatus.PENDING_APPROVAL,
        reason="",
        approved_by="",
        created_at=datetime.utcnow(),
        vectorization_status=VectorizationStatus.PENDING,
        payload={},
        tenant_id=tenant_id,
    )


def _patch_scope(monkeypatch, scope):
    """Patch the endpoint module's scope resolver to return a fixed scope
    (or None), independent of the real ladder (already covered elsewhere)."""
    monkeypatch.setattr(
        "presentation.approval_queue_endpoints.resolve_request_tenant_scope",
        lambda user, client: scope,
    )


def _enqueue_payload() -> EnqueueRequest:
    return EnqueueRequest(
        draft_id="draft-1",
        draft_type="risk_review",
        lines=[JournalLine(account="1105", debit=100, credit=0)],
        memo="test memo",
    )


class TestListDraftsScoping:
    def test_client_list_is_scoped_to_own_tenant(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False))

        recorded = {}

        async def fake_list_drafts(status=None, draft_type=None, tenant_id=None):
            recorded["tenant_id"] = tenant_id
            return [_decision(CLIENT_TENANT_ID)]

        monkeypatch.setattr(ApprovalQueueService, "list_drafts", fake_list_drafts)

        # Even if the client tries to supply a different ?tenant_id, it's ignored.
        response = run(list_drafts(user=_client_user(), tenant_id="some-other-tenant"))

        assert recorded["tenant_id"] == CLIENT_TENANT_ID
        assert len(response.drafts) == 1

    def test_admin_cliente_cero_member_lists_all_tenants(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True))

        recorded = {}

        async def fake_list_drafts(status=None, draft_type=None, tenant_id=None):
            recorded["tenant_id"] = tenant_id
            return [_decision(CLIENTE_CERO_ID)]

        monkeypatch.setattr(ApprovalQueueService, "list_drafts", fake_list_drafts)

        response = run(list_drafts(user=_operator_user(), tenant_id=None))

        assert recorded["tenant_id"] is None
        assert len(response.drafts) == 1

    def test_admin_can_filter_by_tenant_query_param(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True))

        recorded = {}

        async def fake_list_drafts(status=None, draft_type=None, tenant_id=None):
            recorded["tenant_id"] = tenant_id
            return []

        monkeypatch.setattr(ApprovalQueueService, "list_drafts", fake_list_drafts)

        run(list_drafts(user=_operator_user(), tenant_id=CLIENT_TENANT_ID))

        assert recorded["tenant_id"] == CLIENT_TENANT_ID

    def test_authenticated_unresolved_gets_empty_list(self, monkeypatch):
        _patch_scope(monkeypatch, None)

        async def must_not_be_called(status=None, draft_type=None, tenant_id=None):
            raise AssertionError("list_drafts must not be called when scope is None")

        monkeypatch.setattr(ApprovalQueueService, "list_drafts", must_not_be_called)

        response = run(list_drafts(user=_unresolved_user(), tenant_id=None))

        assert response.drafts == []

    def test_list_response_includes_tenant_id_field(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False))

        async def fake_list_drafts(status=None, draft_type=None, tenant_id=None):
            return [_decision(CLIENT_TENANT_ID)]

        monkeypatch.setattr(ApprovalQueueService, "list_drafts", fake_list_drafts)

        response = run(list_drafts(user=_client_user(), tenant_id=None))

        assert response.drafts[0].tenant_id == CLIENT_TENANT_ID


class TestEnqueueScoping:
    def test_enqueue_stamps_callers_resolved_tenant(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False))

        recorded = {}

        async def fake_enqueue_draft(draft_id, draft_type, journal_entry, memo="", *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "enqueue_draft", fake_enqueue_draft)

        response = run(enqueue_for_approval(payload=_enqueue_payload(), user=_client_user()))

        assert recorded["tenant_id"] == CLIENT_TENANT_ID
        assert response.success is True

    def test_staging_identity_enqueues_under_cliente_cero_backcompat(self, monkeypatch):
        # Staging identity resolves to Cliente Cero, all_tenants=True (design.md
        # ladder outcome 4) — same shape as the operator scope.
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True))

        recorded = {}

        async def fake_enqueue_draft(draft_id, draft_type, journal_entry, memo="", *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "enqueue_draft", fake_enqueue_draft)

        run(enqueue_for_approval(payload=_enqueue_payload(), user=dict(_STAGING_USER)))

        assert recorded["tenant_id"] == CLIENTE_CERO_ID

    def test_authenticated_unresolved_enqueue_returns_404_never_cliente_cero(self, monkeypatch):
        _patch_scope(monkeypatch, None)

        async def must_not_be_called(draft_id, draft_type, journal_entry, memo="", *, tenant_id):
            raise AssertionError(
                "enqueue_draft must never be called for an authenticated, unresolved "
                "caller — that would risk enqueuing under Cliente Cero"
            )

        monkeypatch.setattr(ApprovalQueueService, "enqueue_draft", must_not_be_called)

        with pytest.raises(HTTPException) as exc_info:
            run(enqueue_for_approval(payload=_enqueue_payload(), user=_unresolved_user()))

        assert exc_info.value.status_code == 404


class TestApproveRejectScoping:
    def test_approve_passes_caller_tenant_scope(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False))

        recorded = {}

        async def fake_approve_draft(decision_id, approval_reason, approved_by, *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "approve_draft", fake_approve_draft)

        request = ApprovalRequest(decision_id="decision-1", reason="ok", approved_by="a@client.co")
        response = run(approve_draft(request=request, user=_client_user()))

        assert recorded["tenant_id"] == CLIENT_TENANT_ID
        assert response.success is True

    def test_admin_approve_passes_unrestricted_scope(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True))

        recorded = {}

        async def fake_approve_draft(decision_id, approval_reason, approved_by, *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "approve_draft", fake_approve_draft)

        request = ApprovalRequest(decision_id="decision-1", reason="ok", approved_by="ops@contexia.online")
        run(approve_draft(request=request, user=_operator_user()))

        assert recorded["tenant_id"] is None

    def test_approve_unresolved_returns_404(self, monkeypatch):
        _patch_scope(monkeypatch, None)

        async def must_not_be_called(decision_id, approval_reason, approved_by, *, tenant_id):
            raise AssertionError("approve_draft must not be called when scope is None")

        monkeypatch.setattr(ApprovalQueueService, "approve_draft", must_not_be_called)

        request = ApprovalRequest(decision_id="decision-1", reason="ok", approved_by="x@x.co")
        with pytest.raises(HTTPException) as exc_info:
            run(approve_draft(request=request, user=_unresolved_user()))

        assert exc_info.value.status_code == 404

    def test_reject_passes_caller_tenant_scope(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False))

        recorded = {}

        async def fake_reject_draft(decision_id, rejection_reason, rejected_by, *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "reject_draft", fake_reject_draft)

        request = RejectionRequest(decision_id="decision-1", reason="no", rejected_by="a@client.co")
        run(reject_draft(request=request, user=_client_user()))

        assert recorded["tenant_id"] == CLIENT_TENANT_ID

    def test_admin_reject_passes_unrestricted_scope(self, monkeypatch):
        _patch_scope(monkeypatch, TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True))

        recorded = {}

        async def fake_reject_draft(decision_id, rejection_reason, rejected_by, *, tenant_id):
            recorded["tenant_id"] = tenant_id
            return True, _decision(tenant_id), None

        monkeypatch.setattr(ApprovalQueueService, "reject_draft", fake_reject_draft)

        request = RejectionRequest(decision_id="decision-1", reason="no", rejected_by="ops@contexia.online")
        run(reject_draft(request=request, user=_operator_user()))

        assert recorded["tenant_id"] is None

    def test_reject_unresolved_returns_404(self, monkeypatch):
        _patch_scope(monkeypatch, None)

        async def must_not_be_called(decision_id, rejection_reason, rejected_by, *, tenant_id):
            raise AssertionError("reject_draft must not be called when scope is None")

        monkeypatch.setattr(ApprovalQueueService, "reject_draft", must_not_be_called)

        request = RejectionRequest(decision_id="decision-1", reason="no", rejected_by="x@x.co")
        with pytest.raises(HTTPException) as exc_info:
            run(reject_draft(request=request, user=_unresolved_user()))

        assert exc_info.value.status_code == 404
