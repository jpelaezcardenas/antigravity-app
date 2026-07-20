"""
Unit tests for sell_machine_service.py (sell-machine-creative-swarm, Change E).

The orchestration functions (generate -> evaluate -> one-rewrite-pass) are credential-free
(mock copywriter/evaluator). The Approval Queue integration functions are async and mock
ApprovalQueueService directly (no Supabase credentials needed).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.sell_machine_service import (
    create_campaign_package,
    list_campaigns,
    run_creative_loop,
)


def _hook(n=0):
    return {"headline": f"H{n}", "body": f"B{n}", "cta": "C", "pain_tag": "multa_dian"}


class TestRunCreativeLoop:
    def test_approved_hooks_survive_without_rewrite(self):
        hooks = [_hook(1), _hook(2)]
        with patch("services.sell_machine_service.generate_hooks", return_value=hooks), patch(
            "services.sell_machine_service.evaluate_hook", return_value={"approved": True, "reason": "ok"}
        ):
            survivors = run_creative_loop(count=2)

        assert len(survivors) == 2

    def test_rejected_hook_gets_one_rewrite_then_survives_if_it_passes(self):
        hooks = [_hook(1)]
        rewritten = {"headline": "H1-rewritten", "body": "B1", "cta": "C", "pain_tag": "multa_dian"}

        eval_calls = []

        def fake_evaluate(hook):
            eval_calls.append(hook)
            if hook.get("headline") == "H1-rewritten":
                return {"approved": True, "reason": "fixed"}
            return {"approved": False, "reason": "robotic tone"}

        with patch("services.sell_machine_service.generate_hooks", return_value=hooks), patch(
            "services.sell_machine_service.evaluate_hook", side_effect=fake_evaluate
        ), patch("services.sell_machine_service.rewrite_hook", return_value=rewritten) as mock_rewrite:
            survivors = run_creative_loop(count=1)

        mock_rewrite.assert_called_once()
        assert len(survivors) == 1
        assert survivors[0]["headline"] == "H1-rewritten"

    def test_rejected_hook_discarded_if_rewrite_still_fails(self):
        hooks = [_hook(1)]
        with patch("services.sell_machine_service.generate_hooks", return_value=hooks), patch(
            "services.sell_machine_service.evaluate_hook",
            return_value={"approved": False, "reason": "still bad"},
        ), patch("services.sell_machine_service.rewrite_hook", return_value=hooks[0]):
            survivors = run_creative_loop(count=1)

        assert survivors == []

    def test_rewrite_is_attempted_at_most_once_per_hook(self):
        hooks = [_hook(1)]
        with patch("services.sell_machine_service.generate_hooks", return_value=hooks), patch(
            "services.sell_machine_service.evaluate_hook",
            return_value={"approved": False, "reason": "always bad"},
        ) as mock_eval, patch(
            "services.sell_machine_service.rewrite_hook", return_value=hooks[0]
        ) as mock_rewrite:
            run_creative_loop(count=1)

        # Evaluated the original once and the rewrite once = 2 total; rewrite called exactly once.
        assert mock_eval.call_count == 2
        mock_rewrite.assert_called_once()

    def test_default_use_telemetry_false_does_not_fetch_a_report(self):
        """sell-machine-telemetry-loop, Change G: existing callers see no behavior change."""
        hooks = [_hook(1)]
        with patch(
            "services.sell_machine_service.generate_hooks", return_value=hooks
        ) as mock_generate, patch(
            "services.sell_machine_service.evaluate_hook", return_value={"approved": True, "reason": "ok"}
        ), patch("services.sell_machine_service.get_telemetry_report") as mock_report:
            run_creative_loop(count=1)

        mock_report.assert_not_called()
        _, kwargs = mock_generate.call_args
        assert kwargs.get("report") is None

    def test_use_telemetry_true_fetches_and_passes_the_report(self):
        """sell-machine-telemetry-loop, Change G: opt-in report consumption."""
        hooks = [_hook(1)]
        fake_report = {"hook_performance": {"post_content": {"count": 1}}, "funnel_snapshot": {}}
        with patch(
            "services.sell_machine_service.generate_hooks", return_value=hooks
        ) as mock_generate, patch(
            "services.sell_machine_service.evaluate_hook", return_value={"approved": True, "reason": "ok"}
        ), patch(
            "services.sell_machine_service.get_telemetry_report", return_value=fake_report
        ) as mock_report:
            run_creative_loop(count=1, use_telemetry=True)

        mock_report.assert_called_once()
        _, kwargs = mock_generate.call_args
        assert kwargs.get("report") == fake_report


class TestCreateCampaignPackage:
    @pytest.mark.asyncio
    async def test_enqueues_a_campaign_package_draft(self):
        fake_decision = AsyncMock()
        with patch(
            "services.sell_machine_service.ApprovalQueueService.enqueue_draft",
            new=AsyncMock(return_value=(True, fake_decision, None)),
        ) as mock_enqueue:
            result = await create_campaign_package(
                hooks=[_hook(1)], brief="brief", target_segment="asalariados", budget=500000
            )

        assert result is fake_decision
        _, kwargs = mock_enqueue.call_args
        assert kwargs["draft_type"] == "campaign_package"
        assert kwargs["journal_entry"]["hooks"][0]["headline"] == "H1"
        assert kwargs["journal_entry"]["target_segment"] == "asalariados"

    @pytest.mark.asyncio
    async def test_raises_on_enqueue_failure(self):
        with patch(
            "services.sell_machine_service.ApprovalQueueService.enqueue_draft",
            new=AsyncMock(return_value=(False, None, "db error")),
        ):
            with pytest.raises(RuntimeError):
                await create_campaign_package(hooks=[_hook(1)], brief="b", target_segment="s", budget=None)


class TestListCampaigns:
    @pytest.mark.asyncio
    async def test_lists_campaign_package_drafts(self):
        with patch(
            "services.sell_machine_service.ApprovalQueueService.list_drafts",
            new=AsyncMock(return_value=["decision-1", "decision-2"]),
        ) as mock_list:
            result = await list_campaigns(status="pending_approval")

        assert result == ["decision-1", "decision-2"]
        _, kwargs = mock_list.call_args
        assert kwargs["draft_type"] == "campaign_package"
        assert kwargs["status"] == "pending_approval"
