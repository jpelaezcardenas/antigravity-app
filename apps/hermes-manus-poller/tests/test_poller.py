"""Tests for the Hermes->Manus poller.

All network access is mocked; no credentials are needed to run these. Covers the load-bearing
safety properties, not just the happy path:
  - unconfigured node claims NOTHING (fail closed)
  - a task that could not be claimed is never sent to Manus (no double-post)
  - a claimed-but-not-created task becomes a reported orphan, never a silent re-dispatch
  - side-effecting prompts tell Manus the copy is already human-approved
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import backend_client  # noqa: E402
import manus_client  # noqa: E402
import poller  # noqa: E402
import state  # noqa: E402
from config import settings  # noqa: E402
from prompts import (  # noqa: E402
    SIDE_EFFECTING_TASK_TYPES,
    build_manus_prompt,
    build_manus_title,
)


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    """Point the sidecar at a temp dir so tests never touch the real state file."""
    monkeypatch.setattr(state, "_STATE_DIR", tmp_path)
    monkeypatch.setattr(state, "_STATE_FILE", tmp_path / "dispatched.json")
    yield


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch):
    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "MAX_TASKS_PER_TICK", 3)
    yield


def _task(task_id="task-1", task_type="post_content", payload=None, status="pending"):
    return {
        "id": task_id,
        "task_type": task_type,
        "status": status,
        "payload": payload or {"creative_brief": "brief", "hooks": [{"headline": "H1"}]},
    }


# --------------------------------------------------------------------------- prompts


class TestPrompts:
    def test_side_effecting_prompts_state_content_is_human_approved(self):
        for task_type in SIDE_EFFECTING_TASK_TYPES:
            prompt = build_manus_prompt(_task(task_type=task_type))
            assert "YA FUE APROBADO" in prompt
            assert "NO reescribas" in prompt

    def test_run_ads_ab_prompt_forbids_raising_the_budget(self):
        prompt = build_manus_prompt(_task(task_type="run_ads_ab"))
        assert "budget_cents" in prompt
        assert "No lo aumentes" in prompt

    def test_read_only_prompts_forbid_inventing_figures(self):
        for task_type in ("research", "metrics_pull", "generate_doc", "external_integration"):
            prompt = build_manus_prompt(_task(task_type=task_type))
            assert "No inventes cifras" in prompt

    def test_unknown_task_type_forbids_external_side_effects(self):
        prompt = build_manus_prompt(_task(task_type="something_new"))
        assert "no reconocido" in prompt
        assert "No ejecutes ninguna acción con efecto externo" in prompt

    def test_payload_is_included_verbatim(self):
        prompt = build_manus_prompt(_task(payload={"creative_brief": "UNIQUE-MARKER-123"}))
        assert "UNIQUE-MARKER-123" in prompt

    def test_creative_brief_research_task_requests_structured_hooks_output(self):
        prompt = build_manus_prompt(
            _task(task_type="research", payload={"creative_brief": "Renta Natural freelancers"})
        )
        assert '"hooks"' in prompt
        assert "headline" in prompt and "body" in prompt and "cta" in prompt

    def test_non_creative_research_task_prompt_is_unaffected(self):
        prompt = build_manus_prompt(
            _task(task_type="research", payload={"question": "UVT 2026 vigente?"})
        )
        assert '"hooks"' not in prompt

    def test_title_is_short_and_identifies_the_task(self):
        title = build_manus_title(_task(task_id="abcdef1234567890", task_type="research"))
        assert "research" in title
        assert "abcdef12" in title


# --------------------------------------------------------------------------- manus client


class TestManusClient:
    def test_is_configured_reflects_the_api_key(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "")
        assert manus_client.is_configured() is False
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        assert manus_client.is_configured() is True

    def test_create_task_without_key_makes_no_http_call(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "")
        with patch("manus_client.httpx.post") as mock_post:
            assert manus_client.create_task("content", "title") is None
        mock_post.assert_not_called()

    def test_create_task_posts_confirmed_contract(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        response = MagicMock(status_code=200)
        response.json.return_value = {"ok": True, "task_id": "manus-1", "task_url": "https://x"}

        with patch("manus_client.httpx.post", return_value=response) as mock_post:
            result = manus_client.create_task("hello", "My title")

        assert result["task_id"] == "manus-1"
        url = mock_post.call_args[0][0]
        assert url.endswith("/v2/task.create")
        assert mock_post.call_args.kwargs["headers"]["x-manus-api-key"] == "key-123"
        assert mock_post.call_args.kwargs["json"]["message"]["content"] == "hello"

    def test_create_task_handles_not_ok_body(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        response = MagicMock(status_code=200)
        response.json.return_value = {"ok": False}
        with patch("manus_client.httpx.post", return_value=response):
            assert manus_client.create_task("c", "t") is None

    def test_create_task_never_raises_on_network_error(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch("manus_client.httpx.post", side_effect=Exception("boom")):
            assert manus_client.create_task("c", "t") is None

    def test_get_task_maps_status_and_terminality(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        cases = {
            "running": (False, None),
            "waiting": (False, None),
            "stopped": (True, "completed"),
            "error": (True, "failed"),
        }
        for manus_status, (is_terminal, backend_status) in cases.items():
            response = MagicMock(status_code=200)
            response.json.return_value = {
                "ok": True,
                "task": {"id": "m-1", "status": manus_status, "credit_usage": 7},
            }
            with patch("manus_client.httpx.get", return_value=response):
                task = manus_client.get_task("m-1")
            assert task.is_terminal is is_terminal
            if backend_status:
                assert task.backend_status == backend_status

    def test_list_messages_without_key_makes_no_http_call(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "")
        with patch("manus_client.httpx.get") as mock_get:
            assert manus_client.list_messages("m-1") is None
        mock_get.assert_not_called()

    def test_list_messages_returns_the_message_list_on_success(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        response = MagicMock(status_code=200)
        response.json.return_value = {
            "ok": True,
            "task_id": "m-1",
            "messages": [{"type": "assistant_message", "assistant_message": {"content": "hi"}}],
            "has_more": False,
        }
        with patch("manus_client.httpx.get", return_value=response) as mock_get:
            messages = manus_client.list_messages("m-1")

        assert messages == [{"type": "assistant_message", "assistant_message": {"content": "hi"}}]
        url = mock_get.call_args[0][0]
        assert url.endswith("/v2/task.listMessages")
        assert mock_get.call_args.kwargs["params"]["task_id"] == "m-1"

    def test_list_messages_returns_none_on_non_200(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch(
            "manus_client.httpx.get", return_value=MagicMock(status_code=500, text="err")
        ):
            assert manus_client.list_messages("m-1") is None

    def test_list_messages_returns_none_on_not_ok_body(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        response = MagicMock(status_code=200)
        response.json.return_value = {"ok": False}
        with patch("manus_client.httpx.get", return_value=response):
            assert manus_client.list_messages("m-1") is None

    def test_list_messages_never_raises_on_network_error(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch("manus_client.httpx.get", side_effect=Exception("boom")):
            assert manus_client.list_messages("m-1") is None


# --------------------------------------------------------------------------- backend client


class TestBackendClient:
    def test_list_pending_returns_empty_on_failure(self):
        with patch("backend_client.httpx.get", side_effect=Exception("down")):
            assert backend_client.list_pending() == []

    def test_mark_dispatched_false_on_non_200(self):
        with patch("backend_client.httpx.post", return_value=MagicMock(status_code=409, text="no")):
            assert backend_client.mark_dispatched("t-1") is False

    def test_report_result_rejects_invalid_status_without_calling(self):
        with patch("backend_client.httpx.post") as mock_post:
            assert backend_client.report_result("t-1", "bogus", {}) is False
        mock_post.assert_not_called()


# --------------------------------------------------------------------------- tick


class TestRunTick:
    def test_unconfigured_node_claims_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "")
        with patch("backend_client.list_pending") as mock_pending, patch(
            "backend_client.mark_dispatched"
        ) as mock_claim:
            summary = poller.run_tick()

        assert summary["skipped"] == 1
        mock_pending.assert_not_called()
        mock_claim.assert_not_called()

    def test_pending_task_is_claimed_then_dispatched(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch("backend_client.list_pending", return_value=[_task("t-1")]), patch(
            "backend_client.mark_dispatched", return_value=True
        ) as mock_claim, patch(
            "manus_client.create_task", return_value={"task_id": "m-1", "task_url": "u"}
        ) as mock_create:
            summary = poller.run_tick()

        assert summary["dispatched"] == 1
        mock_claim.assert_called_once_with("t-1")
        mock_create.assert_called_once()
        assert state.get_manus_task_id("t-1") == "m-1"

    def test_unclaimable_task_is_never_sent_to_manus(self, monkeypatch):
        """The double-post guard: if the backend refuses the claim, no Manus task is created."""
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch("backend_client.list_pending", return_value=[_task("t-1")]), patch(
            "backend_client.mark_dispatched", return_value=False
        ), patch("manus_client.create_task") as mock_create:
            summary = poller.run_tick()

        assert summary["dispatched"] == 0
        mock_create.assert_not_called()
        assert state.get_manus_task_id("t-1") is None

    def test_claimed_but_create_failed_leaves_no_sidecar_entry(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        with patch("backend_client.list_pending", return_value=[_task("t-1")]), patch(
            "backend_client.mark_dispatched", return_value=True
        ), patch("manus_client.create_task", return_value=None):
            summary = poller.run_tick()

        assert summary["dispatched"] == 0
        assert state.get_manus_task_id("t-1") is None

    def test_respects_max_tasks_per_tick(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        monkeypatch.setattr(settings, "MAX_TASKS_PER_TICK", 2)
        pending = [_task(f"t-{i}") for i in range(5)]
        with patch("backend_client.list_pending", return_value=pending), patch(
            "backend_client.mark_dispatched", return_value=True
        ), patch("manus_client.create_task", return_value={"task_id": "m", "task_url": "u"}):
            summary = poller.run_tick()

        assert summary["dispatched"] == 2

    def test_terminal_manus_task_is_reported_and_forgotten(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        finished = manus_client.ManusTask(
            task_id="m-1", status="stopped", task_url="https://manus/x", credit_usage=12
        )
        with patch("manus_client.get_task", return_value=finished), patch(
            "manus_client.list_messages", return_value=None
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            summary = poller.run_tick()

        assert summary["resolved"] == 1
        assert mock_report.call_args[0][1] == "completed"
        assert mock_report.call_args[0][2]["credit_usage"] == 12
        assert state.get_manus_task_id("t-1") is None

    def test_structured_hooks_result_is_included_in_the_reported_result(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        finished = manus_client.ManusTask(task_id="m-1", status="stopped")
        hooks = [{"headline": "H1", "body": "B1", "cta": "C1", "pain_tag": "multa_dian"}]
        messages = [
            {
                "type": "structured_output_result",
                "structured_output_result": {"success": True, "value": {"hooks": hooks}, "error": None},
            }
        ]
        with patch("manus_client.get_task", return_value=finished), patch(
            "manus_client.list_messages", return_value=messages
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            poller.run_tick()

        reported_result = mock_report.call_args[0][2]
        assert reported_result["hooks"] == hooks
        assert "manus_message" not in reported_result

    def test_last_successful_structured_output_wins_over_an_earlier_failed_one(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        finished = manus_client.ManusTask(task_id="m-1", status="stopped")
        good_hooks = [{"headline": "Good", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        messages = [
            {
                "type": "structured_output_result",
                "structured_output_result": {"success": False, "value": None, "error": "retry"},
            },
            {
                "type": "structured_output_result",
                "structured_output_result": {"success": True, "value": {"hooks": good_hooks}, "error": None},
            },
        ]
        with patch("manus_client.get_task", return_value=finished), patch(
            "manus_client.list_messages", return_value=messages
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            poller.run_tick()

        assert mock_report.call_args[0][2]["hooks"] == good_hooks

    def test_unstructured_output_is_surfaced_as_manus_message_not_hooks(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        finished = manus_client.ManusTask(task_id="m-1", status="stopped")
        messages = [
            {"type": "assistant_message", "assistant_message": {"content": "Investigué la normativa DIAN..."}},
        ]
        with patch("manus_client.get_task", return_value=finished), patch(
            "manus_client.list_messages", return_value=messages
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            poller.run_tick()

        reported_result = mock_report.call_args[0][2]
        assert "hooks" not in reported_result
        assert "Investigué la normativa DIAN" in reported_result["manus_message"]

    def test_list_messages_failure_does_not_affect_the_reported_result(self, monkeypatch):
        """manus_client.list_messages() returning None (its fail-soft contract) must not crash
        the tick or block reporting the base result — same as before this change existed."""
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        finished = manus_client.ManusTask(task_id="m-1", status="stopped", credit_usage=5)
        with patch("manus_client.get_task", return_value=finished), patch(
            "manus_client.list_messages", return_value=None
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            summary = poller.run_tick()

        assert summary["resolved"] == 1
        reported_result = mock_report.call_args[0][2]
        assert "hooks" not in reported_result
        assert "manus_message" not in reported_result
        assert reported_result["credit_usage"] == 5

    def test_error_status_maps_to_failed(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        errored = manus_client.ManusTask(task_id="m-1", status="error")
        with patch("manus_client.get_task", return_value=errored), patch(
            "manus_client.list_messages", return_value=None
        ), patch("backend_client.report_result", return_value=True) as mock_report, patch(
            "backend_client.list_pending", return_value=[]
        ):
            poller.run_tick()

        assert mock_report.call_args[0][1] == "failed"

    def test_in_flight_task_is_left_alone(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        state.remember("t-1", "m-1")
        running = manus_client.ManusTask(task_id="m-1", status="running")
        with patch("manus_client.get_task", return_value=running), patch(
            "backend_client.report_result"
        ) as mock_report, patch("backend_client.list_pending", return_value=[]):
            summary = poller.run_tick()

        assert summary["resolved"] == 0
        mock_report.assert_not_called()
        assert state.get_manus_task_id("t-1") == "m-1"

    def test_dry_run_changes_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "MANUS_API_KEY", "key-123")
        monkeypatch.setattr(settings, "DRY_RUN", True)
        with patch("backend_client.list_pending", return_value=[_task("t-1")]), patch(
            "backend_client.mark_dispatched"
        ) as mock_claim, patch("manus_client.create_task") as mock_create:
            summary = poller.run_tick()

        assert summary["dispatched"] == 0
        mock_claim.assert_not_called()
        mock_create.assert_not_called()


class TestStateSidecar:
    def test_remember_get_forget_roundtrip(self):
        state.remember("t-1", "m-1")
        assert state.get_manus_task_id("t-1") == "m-1"
        state.forget("t-1")
        assert state.get_manus_task_id("t-1") is None

    def test_list_orphans_reports_unknown_dispatched_tasks(self):
        state.remember("t-known", "m-1")
        orphans = state.list_orphans(["t-known", "t-orphan"])
        assert orphans == ["t-orphan"]

    def test_corrupt_state_file_is_treated_as_empty(self):
        state._STATE_DIR.mkdir(parents=True, exist_ok=True)
        state._STATE_FILE.write_text("{not json", encoding="utf-8")
        assert state.all_dispatched() == {}
