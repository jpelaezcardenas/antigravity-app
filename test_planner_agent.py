"""
Test suite for PlannerAgent (Agent 2) with real LLM integration.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from agents.planner_agent import PlannerAgent
from agents.base_agent import AgentRole


class TestPlannerAgent:
    """Test suite for Planner/SEO Strategist Agent"""

    def setup_method(self):
        """Initialize fresh agent for each test"""
        self.agent = PlannerAgent()

    def test_agent_initialization(self):
        """Test PlannerAgent initializes with correct role"""
        assert self.agent.role == AgentRole.SEO_STRATEGIST
        assert self.agent.name == "SEO Strategist Agent"
        assert self.agent.version == "2.0"

    def test_execute_with_valid_input(self):
        """Test execute method returns campaign options"""
        input_data = {
            "campaign_objective": "lead_generation",
            "tax_dna": {
                "verbal_identity": {"tone": "Professional"},
                "servicios": {
                    "primary_services": [
                        {"name": "Consulting"},
                        {"name": "Auditing"},
                        {"name": "Training"}
                    ]
                },
                "buyer_personas": []
            },
            "budget": 5000,
            "timeline_weeks": 4,
            "target_channels": ["instagram", "linkedin"]
        }

        with patch.object(self.agent, 'call_llm', return_value={
            "options": [
                {
                    "name": "Test Campaign 1",
                    "workflow_type": "instagram-calendar",
                    "description": "Test description",
                    "timeline": "4 weeks",
                    "channels": ["instagram"],
                    "posts_count": 16,
                    "budget_allocation": {
                        "content_creation": 1500,
                        "promotion": 3000,
                        "management": 500
                    },
                    "expected_metrics": {
                        "reach": 10000,
                        "engagement": 500,
                        "conversions": 50
                    },
                    "best_for": ["Lead generation"],
                    "difficulty": "Easy",
                    "estimated_roi": 3.5
                }
            ]
        }):
            # execute() returns output directly
            result = self.agent.execute(input_data)

            assert "campaign_options" in result
            assert len(result["campaign_options"]) > 0
            assert "recommendation" in result
            assert "budget_analysis" in result

    def test_generate_options_calls_llm(self):
        """Test that _generate_options uses LLM"""
        objective = "brand_awareness"
        tax_dna = {
            "verbal_identity": {"tone": "Casual"},
            "servicios": {"primary_services": []}
        }
        budget = 3000
        weeks = 4
        channels = ["instagram"]

        mock_llm_response = {
            "options": [
                {
                    "name": "Test Option 1",
                    "workflow_type": "test-workflow",
                    "description": "Test description",
                    "timeline": "4 weeks",
                    "channels": ["instagram"],
                    "posts_count": 12,
                    "budget_allocation": {
                        "content_creation": 900,
                        "promotion": 1800,
                        "management": 300
                    },
                    "expected_metrics": {
                        "reach": 8000,
                        "engagement": 400,
                        "conversions": 40
                    },
                    "best_for": ["Awareness"],
                    "difficulty": "Medium",
                    "estimated_roi": 3.0
                }
            ]
        }

        with patch.object(self.agent, 'call_llm', return_value=mock_llm_response) as mock_llm:
            options = self.agent._generate_options(objective, tax_dna, budget, weeks, channels)

            # Verify LLM was called
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            assert "response_format" in call_args.kwargs
            assert call_args.kwargs["response_format"] == "json"

            # Verify options returned
            assert len(options) > 0
            assert options[0]["option_id"] == 1

    def test_generate_options_fallback_on_parse_error(self):
        """Test fallback when LLM JSON parsing fails"""
        objective = "lead_generation"
        tax_dna = {}
        budget = 5000
        weeks = 4
        channels = ["instagram"]

        # Mock LLM returning parsing error
        with patch.object(self.agent, 'call_llm', return_value={
            "parsing_error": True,
            "status": "fallback"
        }):
            options = self.agent._generate_options(objective, tax_dna, budget, weeks, channels)

            # Should return fallback options
            assert len(options) > 0
            assert "note" in options[0]
            assert "Fallback" in options[0]["note"]

    def test_rank_options_by_objective(self):
        """Test ranking options by objective and ROI"""
        options = [
            {
                "option_id": 1,
                "estimated_roi": 3.5,
                "budget_allocation": {"content": 1000, "promo": 2000, "mgmt": 500}
            },
            {
                "option_id": 2,
                "estimated_roi": 5.2,
                "budget_allocation": {"content": 1000, "promo": 2000, "mgmt": 500}
            },
            {
                "option_id": 3,
                "estimated_roi": 4.0,
                "budget_allocation": {"content": 1000, "promo": 2000, "mgmt": 500}
            }
        ]

        # Rank for "conversion" objective
        ranked = self.agent._rank_options(options, "conversion", 5000)

        # Should have some ranking
        assert len(ranked) > 0
        # Check that options are ranked (higher ROI should generally rank higher)
        if len(ranked) > 1:
            assert ranked[0].get("estimated_roi", 0) >= ranked[1].get("estimated_roi", 0)

    def test_optimize_for_seo(self):
        """Test SEO optimization with LLM"""
        content = "We provide tax consulting services for businesses"
        keywords = ["tax consulting", "business accounting", "compliance"]

        mock_response = {
            "optimized_content": "We provide expert tax consulting and compliance services for growing businesses",
            "meta_title": "Tax Consulting & Business Accounting Services",
            "meta_description": "Professional tax consulting and compliance services for businesses",
            "keyword_variations": ["tax consulting", "tax planning", "business tax services"],
            "integration_quality": 85,
            "seo_score": 78
        }

        with patch.object(self.agent, 'call_llm', return_value=mock_response) as mock_llm:
            result = self.agent.optimize_for_seo(content, keywords)

            # Verify LLM was called
            mock_llm.assert_called_once()

            # Verify response structure
            assert "optimized_content" in result
            assert "meta_title" in result
            assert "meta_description" in result
            assert "seo_score" in result

    def test_optimize_for_seo_fallback(self):
        """Test SEO optimization fallback when LLM fails"""
        content = "We provide tax consulting"
        keywords = ["tax", "consulting"]

        with patch.object(self.agent, 'call_llm', return_value={
            "parsing_error": True
        }):
            result = self.agent.optimize_for_seo(content, keywords)

            # Should return fallback
            assert "note" in result
            assert "Fallback" in result["note"]
            assert result["seo_score"] == 50

    def test_generate_hashtags_instagram(self):
        """Test hashtag generation for Instagram"""
        content = "Check out our latest marketing tips for small business owners"
        platform = "instagram"
        count = 10

        mock_response = {
            "hashtags": [
                "#marketingtips", "#smallbusiness", "#businessgrowth",
                "#instagram", "#contentmarketing", "#socialmedia",
                "#entrepreneurship", "#brandingagency", "#marketingagency", "#insta"
            ],
            "trending": ["#marketingtips", "#smallbusiness", "#businessgrowth"],
            "niche": ["#marketingagency", "#brandingagency"],
            "strategy": "Mix of high-volume trending + niche audience tags",
            "estimated_reach": "high",
            "platform_recommendations": "Use hashtags in first comment for best engagement"
        }

        with patch.object(self.agent, 'call_llm', return_value=mock_response) as mock_llm:
            result = self.agent.generate_hashtags(content, platform, count)

            # Verify LLM was called with correct platform
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            assert platform in str(call_args)

            # Verify response structure
            assert "hashtags" in result
            assert "trending" in result
            assert "niche" in result
            assert "strategy" in result
            assert len(result["hashtags"]) <= count

    def test_generate_hashtags_linkedin(self):
        """Test hashtag generation for LinkedIn"""
        content = "Professional development tips for managers"
        platform = "linkedin"
        count = 8

        mock_response = {
            "hashtags": [
                "#leadership", "#management", "#businessgrowth",
                "#entrepreneurship", "#marketingtips", "#professional",
                "#careerdevelopment", "#linkedinnews"
            ],
            "trending": ["#leadership", "#management"],
            "niche": ["#linkedinnews", "#careerdevelopment"],
            "strategy": "Professional and business-focused hashtags",
            "estimated_reach": "medium",
            "platform_recommendations": "LinkedIn limit is 30 characters per tag, use 3-5 tags max"
        }

        with patch.object(self.agent, 'call_llm', return_value=mock_response):
            result = self.agent.generate_hashtags(content, platform, count)

            assert "hashtags" in result
            assert result["estimated_reach"] in ["low", "medium", "high"]

    def test_generate_hashtags_fallback(self):
        """Test hashtag generation fallback when LLM fails"""
        content = "Test content"
        platform = "instagram"
        count = 10

        with patch.object(self.agent, 'call_llm', return_value={
            "parsing_error": True
        }):
            result = self.agent.generate_hashtags(content, platform, count)

            # Should return fallback hashtags
            assert "hashtags" in result
            assert len(result["hashtags"]) > 0
            assert "note" in result
            assert "Fallback" in result["note"]

    def test_campaign_options_fallback(self):
        """Test fallback campaign options method"""
        options = self.agent._campaign_options_fallback(budget=5000, weeks=4, channels=["instagram"])

        assert len(options) > 0
        assert options[0]["option_id"] == 1
        assert "workflow_type" in options[0]
        assert "estimated_roi" in options[0]
        assert "note" in options[0]

    def test_analyze_budget(self):
        """Test budget analysis"""
        result = self.agent._analyze_budget(total_budget=5000, num_options=3)

        assert result["total_budget"] == 5000
        assert result["per_option_budget"] == pytest.approx(5000 / 3)
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert result["budget_sufficient"] is True


class TestPlannerAgentIntegration:
    """Integration tests for PlannerAgent"""

    def test_full_campaign_generation_flow(self):
        """Test complete campaign generation flow"""
        agent = PlannerAgent()

        input_data = {
            "campaign_objective": "lead_generation",
            "tax_dna": {
                "verbal_identity": {"tone": "Professional"},
                "servicios": {
                    "primary_services": [
                        {"name": "Tax Consulting"},
                        {"name": "Auditing"},
                        {"name": "Compliance"}
                    ]
                },
                "buyer_personas": []
            },
            "budget": 5000,
            "timeline_weeks": 4,
            "target_channels": ["instagram", "linkedin"]
        }

        # Mock LLM responses for multiple calls
        with patch.object(agent, 'call_llm', return_value={
            "options": [
                {
                    "name": "Lead Gen Campaign",
                    "workflow_type": "lead-generation",
                    "description": "Optimized for lead capture",
                    "timeline": "4 weeks",
                    "channels": ["instagram", "linkedin"],
                    "posts_count": 20,
                    "budget_allocation": {
                        "content_creation": 1500,
                        "promotion": 3000,
                        "management": 500
                    },
                    "expected_metrics": {
                        "reach": 15000,
                        "engagement": 750,
                        "conversions": 75
                    },
                    "best_for": ["Lead generation", "Sales pipeline"],
                    "difficulty": "Medium",
                    "estimated_roi": 4.5
                }
            ]
        }):
            # execute() returns output directly
            result = agent.execute(input_data)

            assert "campaign_options" in result
            assert len(result["campaign_options"]) > 0

    def test_seo_and_hashtag_pipeline(self):
        """Test SEO optimization + hashtag generation pipeline"""
        agent = PlannerAgent()
        content = "Amazing tax tips for small business owners"

        # Mock for SEO optimization
        seo_mock = {
            "optimized_content": "Valuable tax optimization strategies for small business owners",
            "meta_title": "Tax Tips for Small Business Owners",
            "meta_description": "Proven tax strategies for small business",
            "keyword_variations": ["tax tips", "business tax", "tax optimization"],
            "integration_quality": 90,
            "seo_score": 85
        }

        # Mock for hashtag generation
        hashtags_mock = {
            "hashtags": ["#taxtips", "#smallbusiness", "#businesstax"],
            "trending": ["#taxips", "#smallbusiness"],
            "niche": ["#taxaccounting"],
            "strategy": "Mix of tax and business hashtags",
            "estimated_reach": "high",
            "platform_recommendations": "Use in first comment"
        }

        with patch.object(agent, 'call_llm', side_effect=[seo_mock, hashtags_mock]):
            seo_result = agent.optimize_for_seo(content, ["tax", "small business"])
            hashtag_result = agent.generate_hashtags(content, "instagram")

            assert seo_result["seo_score"] >= 0
            assert len(hashtag_result["hashtags"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
