"""
Tests for operator task endpoints (hermes-manus-execution-bridge, Change F).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_sell_machine_endpoints.py. These routes
live in presentation/sell_machine_endpoints.py (extended, not a new module — see design.md
Decision/tasks.md 4.2) and share the same SELL_MACHINE_CANONICAL-gated router.
"""

from __future__ import annotations

from typing import Dict, Optional
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def sm_client():
    from presentation.sell_machine_endpoints import router as sell_machine_router

    app = FastAPI()
    app.include_router(sell_machine_router, prefix="/sell-machine")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture(autouse=True)
def _patch_agent_operations_logger():
    """The 4 mutating operator-task endpoints record a best-effort audit entry via the shared
    `agent_operations_logger` instance; patch it globally in this module so existing tests that
    don't care about audit recording aren't broken by unmocked real Supabase calls."""
    with patch(
        "presentation.sell_machine_endpoints.agent_operations_logger.record",
        new=AsyncMock(return_value=True),
    ) as mock_record:
        yield mock_record


class TestListPendingTasksEndpoint:
    @pytest.mark.asyncio
    async def test_returns_pending_tasks(self, sm_client) -> None:
        fake_tasks = [{"id": "task-1", "task_type": "research", "status": "pending", "payload": {}}]
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.list_pending_tasks", return_value=fake_tasks
            ):
                response = await client.get("/sell-machine/tasks/pending")

        assert response.status_code == 200
        assert response.json() == fake_tasks

    @pytest.mark.asyncio
    async def test_forwards_tenant_id_query_param(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.list_pending_tasks", return_value=[]
            ) as mock_list:
                response = await client.get("/sell-machine/tasks/pending?tenant_id=tenant-1")

        assert response.status_code == 200
        mock_list.assert_called_once_with(tenant_id="tenant-1")


class TestCreateTaskEndpoint:
    @pytest.mark.asyncio
    async def test_creates_a_read_only_task(self, sm_client) -> None:
        fake_row = {
            "id": "task-1",
            "task_type": "research",
            "status": "pending",
            "payload": {},
            "tenant_id": "tenant-1",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_task",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks", json={"task_type": "research", "payload": {}}
                )

        assert response.status_code == 200
        assert response.json()["task_type"] == "research"

    @pytest.mark.asyncio
    async def test_forwards_tenant_id_when_provided(self, sm_client) -> None:
        fake_row = {
            "id": "task-1",
            "task_type": "research",
            "status": "pending",
            "payload": {},
            "tenant_id": "tenant-1",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_task",
                return_value=(True, fake_row, None),
            ) as mock_create:
                response = await client.post(
                    "/sell-machine/tasks",
                    json={"task_type": "research", "payload": {}, "tenant_id": "tenant-1"},
                )

        assert response.status_code == 200
        mock_create.assert_called_once_with(
            task_type="research", payload={}, tenant_id="tenant-1"
        )

    @pytest.mark.asyncio
    async def test_forwards_none_tenant_id_when_omitted(self, sm_client) -> None:
        fake_row = {
            "id": "task-1",
            "task_type": "research",
            "status": "pending",
            "payload": {},
            "tenant_id": "tenant-1",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_task",
                return_value=(True, fake_row, None),
            ) as mock_create:
                response = await client.post(
                    "/sell-machine/tasks", json={"task_type": "research", "payload": {}}
                )

        assert response.status_code == 200
        mock_create.assert_called_once_with(task_type="research", payload={}, tenant_id=None)

    @pytest.mark.asyncio
    async def test_rejects_side_effecting_task_type_with_400(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_task",
                return_value=(False, None, "task_type 'post_content' is side-effecting"),
            ):
                response = await client.post(
                    "/sell-machine/tasks", json={"task_type": "post_content", "payload": {}}
                )

        assert response.status_code == 400


class TestDispatchCampaignEndpoint:
    @pytest.mark.asyncio
    async def test_dispatches_an_approved_campaign(self, sm_client) -> None:
        fake_row = {
            "id": "task-1",
            "task_type": "post_content",
            "status": "pending",
            "tenant_id": "tenant-1",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.dispatch_campaign_package",
                new=AsyncMock(return_value=(True, fake_row, None)),
            ):
                response = await client.post("/sell-machine/campaigns/decision-1/dispatch")

        assert response.status_code == 200
        assert response.json()["task_type"] == "post_content"

    @pytest.mark.asyncio
    async def test_returns_400_when_decision_not_approved(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.dispatch_campaign_package",
                new=AsyncMock(return_value=(False, None, "decision decision-1 is 'pending_approval'")),
            ):
                response = await client.post("/sell-machine/campaigns/decision-1/dispatch")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_404_when_decision_not_found(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.dispatch_campaign_package",
                new=AsyncMock(return_value=(False, None, "decision decision-1 not found")),
            ):
                response = await client.post("/sell-machine/campaigns/decision-1/dispatch")

        assert response.status_code == 404


class TestTaskStatusEndpoint:
    @pytest.mark.asyncio
    async def test_marks_dispatched(self, sm_client) -> None:
        fake_row = {"id": "task-1", "status": "dispatched", "tenant_id": "tenant-1"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.mark_dispatched",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/status", json={"status": "dispatched"}
                )

        assert response.status_code == 200
        assert response.json()["status"] == "dispatched"

    @pytest.mark.asyncio
    async def test_returns_409_on_invalid_transition(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.mark_dispatched",
                return_value=(False, None, "task task-1 is 'dispatched', not 'pending'"),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/status", json={"status": "dispatched"}
                )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_returns_404_when_task_not_found(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.mark_dispatched",
                return_value=(False, None, "task task-1 not found"),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/status", json={"status": "dispatched"}
                )

        assert response.status_code == 404


class TestTaskResultEndpoint:
    @pytest.mark.asyncio
    async def test_reports_a_completed_result(self, sm_client) -> None:
        fake_row = {
            "id": "task-1",
            "status": "completed",
            "result": {"post_url": "https://x"},
            "tenant_id": "tenant-1",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.report_result",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/result",
                    json={"status": "completed", "result": {"post_url": "https://x"}},
                )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_returns_409_when_task_not_dispatched(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.report_result",
                return_value=(False, None, "task task-1 is 'pending', not 'dispatched'"),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/result",
                    json={"status": "completed", "result": {}},
                )

        assert response.status_code == 409


class TestHermesBridgeToken:
    """`HERMES_BRIDGE_TOKEN` unset -> all 5 endpoints behave exactly as today (open). Set ->
    missing/incorrect Authorization header is rejected with 401; a correct `Bearer <token>`
    proceeds as normal. `settings.HERMES_BRIDGE_TOKEN` is monkeypatched (read at call time in the
    dependency, not at import time) rather than patching the module attribute directly, so this
    exercises the real production code path."""

    _routes = [
        ("GET", "/sell-machine/tasks/pending", None, "presentation.sell_machine_endpoints.list_pending_tasks", [], {}),
        (
            "POST",
            "/sell-machine/tasks",
            {"task_type": "research", "payload": {}},
            "presentation.sell_machine_endpoints.create_task",
            [(True, {"id": "task-1", "tenant_id": "tenant-1"}, None)],
            {},
        ),
        (
            "POST",
            "/sell-machine/campaigns/decision-1/dispatch",
            None,
            "presentation.sell_machine_endpoints.dispatch_campaign_package",
            [(True, {"id": "task-1", "tenant_id": "tenant-1"}, None)],
            {"is_async": True},
        ),
        (
            "POST",
            "/sell-machine/tasks/task-1/status",
            {"status": "dispatched"},
            "presentation.sell_machine_endpoints.mark_dispatched",
            [(True, {"id": "task-1", "tenant_id": "tenant-1"}, None)],
            {},
        ),
        (
            "POST",
            "/sell-machine/tasks/task-1/result",
            {"status": "completed", "result": {}},
            "presentation.sell_machine_endpoints.report_result",
            [(True, {"id": "task-1", "tenant_id": "tenant-1"}, None)],
            {},
        ),
    ]

    def _mock_for(self, target: str, return_value, is_async: bool):
        if is_async:
            return patch(target, new=AsyncMock(return_value=return_value))
        return patch(target, return_value=return_value)

    def _fresh_client(self):
        """A new AsyncClient per call — `async with client` closes the client on exit, so a
        loop over routes needs a fresh instance per iteration rather than reusing the shared
        `sm_client` fixture (which is single-use)."""
        from presentation.sell_machine_endpoints import router as sell_machine_router

        app = FastAPI()
        app.include_router(sell_machine_router, prefix="/sell-machine")
        transport = httpx.ASGITransport(app=app)
        return httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def _request_each_route(self, headers: Optional[Dict[str, str]] = None):
        responses = []
        for method, path, json_body, target, return_args, opts in self._routes:
            async with self._fresh_client() as client:
                with self._mock_for(
                    target,
                    return_args[0] if return_args else [],
                    opts.get("is_async", False),
                ):
                    response = await client.request(
                        method, path, json=json_body, headers=headers
                    )
            responses.append((method, path, response))
        return responses

    @pytest.mark.asyncio
    async def test_token_unset_preserves_open_behavior(self) -> None:
        with patch("presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", None):
            responses = await self._request_each_route()
        for method, path, response in responses:
            assert response.status_code == 200, f"{method} {path} -> {response.status_code}"

    @pytest.mark.asyncio
    async def test_token_set_rejects_missing_header(self) -> None:
        with patch("presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"):
            responses = await self._request_each_route()
        for method, path, response in responses:
            assert response.status_code == 401, f"{method} {path} -> {response.status_code}"

    @pytest.mark.asyncio
    async def test_token_set_rejects_wrong_token(self) -> None:
        with patch("presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"):
            responses = await self._request_each_route(
                headers={"Authorization": "Bearer wrong-token"}
            )
        for method, path, response in responses:
            assert response.status_code == 401, f"{method} {path} -> {response.status_code}"

    @pytest.mark.asyncio
    async def test_token_set_accepts_correct_bearer_token(self) -> None:
        with patch("presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"):
            responses = await self._request_each_route(
                headers={"Authorization": "Bearer secret-token"}
            )
        for method, path, response in responses:
            assert response.status_code == 200, f"{method} {path} -> {response.status_code}"


class TestAuditRecording:
    """The 4 mutating operator-task endpoints record a best-effort agent_operations entry via
    the shared agent_operations_logger; the poll endpoint (GET /tasks/pending) does not."""

    @pytest.mark.asyncio
    async def test_create_task_records_audit_entry(
        self, sm_client, _patch_agent_operations_logger
    ) -> None:
        fake_row = {"id": "task-1", "task_type": "research", "status": "pending", "tenant_id": "tenant-1"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_task",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks", json={"task_type": "research", "payload": {}}
                )

        assert response.status_code == 200
        _patch_agent_operations_logger.assert_called_once()
        call_kwargs = _patch_agent_operations_logger.call_args.kwargs
        assert call_kwargs["agent_name"] == "hermes-bridge"
        assert call_kwargs["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    async def test_dispatch_campaign_records_audit_entry(
        self, sm_client, _patch_agent_operations_logger
    ) -> None:
        fake_row = {"id": "task-1", "task_type": "post_content", "tenant_id": "tenant-1"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.dispatch_campaign_package",
                new=AsyncMock(return_value=(True, fake_row, None)),
            ):
                response = await client.post("/sell-machine/campaigns/decision-1/dispatch")

        assert response.status_code == 200
        _patch_agent_operations_logger.assert_called_once()
        call_kwargs = _patch_agent_operations_logger.call_args.kwargs
        assert call_kwargs["agent_name"] == "hermes-bridge"
        assert call_kwargs["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    async def test_task_status_records_audit_entry(
        self, sm_client, _patch_agent_operations_logger
    ) -> None:
        fake_row = {"id": "task-1", "status": "dispatched", "tenant_id": "tenant-1"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.mark_dispatched",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/status", json={"status": "dispatched"}
                )

        assert response.status_code == 200
        _patch_agent_operations_logger.assert_called_once()
        call_kwargs = _patch_agent_operations_logger.call_args.kwargs
        assert call_kwargs["agent_name"] == "hermes-bridge"
        assert call_kwargs["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    async def test_task_result_records_audit_entry(
        self, sm_client, _patch_agent_operations_logger
    ) -> None:
        fake_row = {"id": "task-1", "status": "completed", "tenant_id": "tenant-1"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.report_result",
                return_value=(True, fake_row, None),
            ):
                response = await client.post(
                    "/sell-machine/tasks/task-1/result",
                    json={"status": "completed", "result": {}},
                )

        assert response.status_code == 200
        _patch_agent_operations_logger.assert_called_once()
        call_kwargs = _patch_agent_operations_logger.call_args.kwargs
        assert call_kwargs["agent_name"] == "hermes-bridge"
        assert call_kwargs["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    async def test_list_pending_tasks_does_not_record_audit_entry(
        self, sm_client, _patch_agent_operations_logger
    ) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.list_pending_tasks", return_value=[]
            ):
                response = await client.get("/sell-machine/tasks/pending")

        assert response.status_code == 200
        _patch_agent_operations_logger.assert_not_called()
