"""Unit tests for tenant_id stamping at write time (hermes-multi-tenant-wrapper,
Ground Truth Correction #3).

Covers the root-cause fix: ApprovalQueueService.enqueue_draft and CentinelaService.save_alerts
previously never stamped tenant_id on inserted rows, relying purely on ungrounded column
defaults. All Supabase access is mocked at the service-role client getter, matching the pattern
established by test_operator_task_service.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.approval_queue_service import ApprovalQueueService
from services.centinela_service import CentinelaService
from core.tenant_context import TenantResolutionError


def _mock_client_with_tenant(tenant_id: str = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"):
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": tenant_id
    }
    return client


# NOTE: ApprovalQueueService.enqueue_draft has the identical implicit-Cliente-Cero
# stamp as CentinelaService.save_alerts did before centinela-tenant-scoped-alerts.
# This test class is left untouched here — it is the target of a future sibling
# change (approval-queue-tenant-scoped-writes) that adopts require_tenant_id /
# resolve_caller_tenant from core/tenant_context.py. See design.md §9.
class TestEnqueueDraftStampsTenantId:
    @pytest.mark.asyncio
    async def test_stamps_explicitly_passed_tenant_id_on_insert(self):
        """enqueue_draft no longer resolves Cliente Cero itself — it stamps
        whatever tenant_id the caller explicitly passes in."""
        client = MagicMock()
        client.table.return_value.insert.return_value.execute.return_value.data = [{}]

        explicit_tenant_id = "a1b2c3d4-0000-0000-0000-000000000001"

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ), patch(
            "core.tenant_context.resolve_cliente_cero_tenant_id"
        ) as mock_resolve:
            success, decision, error = await ApprovalQueueService.enqueue_draft(
                draft_id="draft-1",
                draft_type="risk_review",
                journal_entry={"risk_score": 91},
                tenant_id=explicit_tenant_id,
            )

        assert success is True
        assert error is None
        assert decision.tenant_id == explicit_tenant_id

        insert_call_args = client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == explicit_tenant_id

        # The service must no longer resolve Cliente Cero internally.
        mock_resolve.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_tenant_id_returns_error_not_silent_insert(self):
        client = MagicMock()
        client.table.return_value.insert.return_value.execute.return_value.data = [{}]

        with patch(
            "services.approval_queue_service.get_service_supabase", return_value=client
        ):
            success, decision, error = await ApprovalQueueService.enqueue_draft(
                draft_id="draft-2",
                draft_type="risk_review",
                journal_entry={"risk_score": 50},
                tenant_id=None,
            )

        assert success is False
        assert decision is None
        assert error == "tenant_id is required"

        client.table.return_value.insert.assert_not_called()


class TestSaveAlertsStampsTenantId:
    """save_alerts is now fail-loud: tenant_id is a required parameter and is
    never resolved from Cliente Cero implicitly (centinela-tenant-scoped-alerts).
    """

    def test_save_alerts_stamps_required_tenant_id(self):
        client = _mock_client_with_tenant()
        client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "alert-1"}
        ]

        service = CentinelaService()
        with patch("services.centinela_service.get_service_supabase", return_value=client):
            saved_ids = service.save_alerts(
                [{"rule_id": "R001", "company_id": "ctx-001", "severity": "warning"}],
                tenant_id="tenant-medic",
            )

        assert saved_ids == ["alert-1"]
        insert_call_args = client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "tenant-medic"
        # No Cliente Cero lookup should occur — the parameter is authoritative.
        client.table.return_value.select.assert_not_called()

    def test_save_alerts_raises_without_tenant_id(self):
        client = _mock_client_with_tenant()
        service = CentinelaService()

        with patch("services.centinela_service.get_service_supabase", return_value=client):
            for missing in (None, ""):
                with pytest.raises(TenantResolutionError):
                    service.save_alerts(
                        [{"rule_id": "R001", "company_id": "ctx-001", "severity": "warning"}],
                        tenant_id=missing,
                    )

        client.table.return_value.insert.assert_not_called()

    def test_save_alerts_parameter_overrides_per_alert_tenant_id(self):
        client = _mock_client_with_tenant()
        client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "alert-1"}
        ]

        service = CentinelaService()
        with patch("services.centinela_service.get_service_supabase", return_value=client):
            service.save_alerts(
                [
                    {
                        "rule_id": "R001",
                        "company_id": "ctx-001",
                        "severity": "warning",
                        "tenant_id": "other-tenant",
                    }
                ],
                tenant_id="tenant-medic",
            )

        insert_call_args = client.table.return_value.insert.call_args[0][0]
        assert insert_call_args["tenant_id"] == "tenant-medic"
