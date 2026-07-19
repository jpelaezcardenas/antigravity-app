"""
Tests for operator task endpoints (hermes-manus-execution-bridge, Change F).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_sell_machine_endpoints.py. These routes
live in presentation/sell_machine_endpoints.py (extended, not a new module — see design.md
Decision/tasks.md 4.2) and share the same SELL_MACHINE_CANONICAL-gated router.
"""

from __future__ import annotations

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


class TestCreateTaskEndpoint:
    @pytest.mark.asyncio
    async def test_creates_a_read_only_task(self, sm_client) -> None:
        fake_row = {"id": "task-1", "task_type": "research", "status": "pending", "payload": {}}
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
        fake_row = {"id": "task-1", "task_type": "post_content", "status": "pending"}
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
        fake_row = {"id": "task-1", "status": "dispatched"}
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
        fake_row = {"id": "task-1", "status": "completed", "result": {"post_url": "https://x"}}
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
