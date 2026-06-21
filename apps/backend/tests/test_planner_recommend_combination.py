"""Tests for PlannerAgent.recommend_combination and helpers (bugs 5 & 9)."""
from agents.planner_agent import PlannerAgent


def test_parse_weeks_handles_strings_and_numbers():
    assert PlannerAgent._parse_weeks("6 weeks") == 6
    assert PlannerAgent._parse_weeks("4 semanas") == 4
    assert PlannerAgent._parse_weeks(8) == 8
    assert PlannerAgent._parse_weeks("no number", default=3) == 3
    assert PlannerAgent._parse_weeks(None, default=2) == 2


def test_recommend_combination_empty_objectives_does_not_crash():
    agent = PlannerAgent()
    result = agent.recommend_combination([], budget=1000)
    assert result["combination"] == {}
    assert result["duration_weeks"] == 0
    assert result["total_posts"] == 0
    assert result["total_roi"] == 0.0


def test_rank_options_skips_options_without_option_id():
    agent = PlannerAgent()
    options = [{"workflow_type": "x", "estimated_roi": 1.0, "budget_allocation": {"a": 1}}]
    # No KeyError even though option_id is missing.
    assert agent._rank_options(options, "general", 100) == []


def test_recommend_combination_returns_numeric_duration(monkeypatch):
    agent = PlannerAgent()
    crafted = [
        {
            "option_id": 1,
            "workflow_type": "wf1",
            "estimated_roi": 3.0,
            "timeline": "6 weeks",
            "posts_count": 12,
            "budget_allocation": {"a": 100},
        },
        {
            "option_id": 4,
            "workflow_type": "wf4",
            "estimated_roi": 5.0,
            "timeline": "8 weeks",
            "posts_count": 20,
            "budget_allocation": {"a": 100},
        },
    ]
    # Avoid any real LLM call; _rank_options runs for real.
    monkeypatch.setattr(agent, "_generate_options", lambda *a, **k: crafted)

    result = agent.recommend_combination(["awareness"], budget=1000)
    assert result["duration_weeks"] == 8  # numeric max of parsed weeks
    assert isinstance(result["duration_weeks"], int)
    assert result["total_posts"] == 20
    assert result["total_roi"] == 5.0
