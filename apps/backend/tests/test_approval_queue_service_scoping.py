"""Unit tests for tenant scoping on approve_draft / reject_draft (approval-queue-tenant-scoping).

Covers the service-layer contract in
openspec/changes/approval-queue-tenant-scoping/design.md: when a caller passes a
concrete tenant_id, both the existence-check SELECT and the UPDATE must filter by
tenant_id, and a cross-tenant decision_id must return the same "not found" error as
a genuinely missing one (never leak cross-tenant existence). When tenant_id is None,
the calls are unrestricted (admin/operator path).

All Supabase access is mocked at the service-role client getter, matching the pattern
established by test_tenant_stamping.py / test_operator_task_service.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.approval_queue_service import ApprovalQueueService


def _mock_client_for_approve(row_data=None):
    """Build a MagicMock Supabase client whose select/update chains are
    independently trackable (separate MagicMock chains per call), while still
    recording every .eq() call made on each chain so tests can assert on them.
    """
    client = MagicMock()

    select_result = MagicMock()
    select_result.data = [row_data] if row_data is not None else []

    update_result = MagicMock()
    update_result.data = [row_data] if row_data is not None else []

    select_chain = client.table.return_value.select.return_value
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = select_result

    update_chain = client.table.return_value.update.return_value
    update_chain.eq.return_value = update_chain
    update_chain.execute.return_value = update_result

    return client


class TestApproveDraftTenantScoping:
    @pytest.mark.asyncio
    async def test_approve_with_tenant_scope_filters_select_and_update_by_tenant(self):
        decision_id = "decision-1"
        tenant_id = "tenant-a"
        row = {
            "id": decision_id,
            "draft_id": "draft-1",
            "draft_type": "risk_review",
            "status": "approved",
            "reason": "ok",
            "approved_by": "operator@contexia.online",
            "created_at": "2026-07-23T00:00:00Z",
            "vectorization_status": "pending",
            "payload": {},
            "tenant_id": tenant_id,
        }
        client = _mock_client_for_approve(row)

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                decision_id=decision_id,
                approval_reason="ok",
                approved_by="operator@contexia.online",
                tenant_id=tenant_id,
            )

        assert success is True
        assert error is None

        select_chain = client.table.return_value.select.return_value
        select_eq_calls = [c.args for c in select_chain.eq.call_args_list]
        assert ("id", decision_id) in select_eq_calls
        assert ("tenant_id", tenant_id) in select_eq_calls

        update_chain = client.table.return_value.update.return_value
        update_eq_calls = [c.args for c in update_chain.eq.call_args_list]
        assert ("id", decision_id) in update_eq_calls
        assert ("tenant_id", tenant_id) in update_eq_calls

    @pytest.mark.asyncio
    async def test_approve_cross_tenant_returns_not_found(self):
        decision_id = "decision-2"
        # Simulate the row existing under a *different* tenant: with tenant_id
        # scoping applied, the select returns no matching row.
        client = _mock_client_for_approve(row_data=None)

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                decision_id=decision_id,
                approval_reason="ok",
                approved_by="operator@contexia.online",
                tenant_id="tenant-b",
            )

        assert success is False
        assert decision is None
        assert error == f"Decision {decision_id} not found"

    @pytest.mark.asyncio
    async def test_approve_with_none_scope_is_unrestricted(self):
        decision_id = "decision-3"
        row = {
            "id": decision_id,
            "draft_id": "draft-3",
            "draft_type": "risk_review",
            "status": "approved",
            "reason": "ok",
            "approved_by": "operator@contexia.online",
            "created_at": "2026-07-23T00:00:00Z",
            "vectorization_status": "pending",
            "payload": {},
            "tenant_id": "tenant-a",
        }
        client = _mock_client_for_approve(row)

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ):
            success, decision, error = await ApprovalQueueService.approve_draft(
                decision_id=decision_id,
                approval_reason="ok",
                approved_by="operator@contexia.online",
                tenant_id=None,
            )

        assert success is True
        assert error is None

        select_chain = client.table.return_value.select.return_value
        select_eq_calls = [c.args for c in select_chain.eq.call_args_list]
        assert all(call[0] != "tenant_id" for call in select_eq_calls)

        update_chain = client.table.return_value.update.return_value
        update_eq_calls = [c.args for c in update_chain.eq.call_args_list]
        assert all(call[0] != "tenant_id" for call in update_eq_calls)


class TestRejectDraftTenantScoping:
    @pytest.mark.asyncio
    async def test_reject_with_tenant_scope_filters_by_tenant(self):
        decision_id = "decision-4"
        tenant_id = "tenant-a"
        row = {
            "id": decision_id,
            "draft_id": "draft-4",
            "draft_type": "risk_review",
            "status": "rejected",
            "reason": "no",
            "approved_by": "operator@contexia.online",
            "created_at": "2026-07-23T00:00:00Z",
            "vectorization_status": "pending",
            "payload": {},
            "tenant_id": tenant_id,
        }
        client = _mock_client_for_approve(row)

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ):
            success, decision, error = await ApprovalQueueService.reject_draft(
                decision_id=decision_id,
                rejection_reason="no",
                rejected_by="operator@contexia.online",
                tenant_id=tenant_id,
            )

        assert success is True
        assert error is None

        select_chain = client.table.return_value.select.return_value
        select_eq_calls = [c.args for c in select_chain.eq.call_args_list]
        assert ("id", decision_id) in select_eq_calls
        assert ("tenant_id", tenant_id) in select_eq_calls

        update_chain = client.table.return_value.update.return_value
        update_eq_calls = [c.args for c in update_chain.eq.call_args_list]
        assert ("id", decision_id) in update_eq_calls
        assert ("tenant_id", tenant_id) in update_eq_calls
