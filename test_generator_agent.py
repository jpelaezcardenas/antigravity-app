"""
Test suite for GeneratorAgent (Agent 3) with real LLM integration.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from agents.generator_agent import GeneratorAgent
from agents.base_agent import AgentRole


class TestGeneratorAgent:
    """Test suite for Content Generator Agent"""

    def setup_method(self):
        """Initialize fresh agent for each test"""
        self.agent = GeneratorAgent()

    def test_agent_initialization(self):
        """Test GeneratorAgent initializes with correct role"""
        assert self.agent.role == AgentRole.GENERATOR
        assert self.agent.name == "Content Generator Agent"
        assert self.agent.version == "2.0"

    def test_execute_with_valid_input(self):
        """Test execute method returns content variations"""
        input_data = {
            "campaign": {
                "id": "camp-123",
                "objective": "lead_generation"
            },
            "tax_dna": {
                "verbal_identity": {
                    "tone": "Professional",
                    "key_phrases": ["tax", "audit", "compliance"]
                },
                "servicios": {
                    "primary_services": [
                        {"name": "Tax Consulting"},
                        {"name": "Auditing"}
                    ]
                },
                "buyer_personas": [
                    {"name": "Small Business Owner"}
                ],
                "compliance_rules": {}
            },
            "channel": "instagram",
            "tone": "Professional",
            "variations_count": 3
        }

        with patch.object(self.agent, 'call_llm', return_value={
            "variations": [
                {
                    "title": "Discover Tax Savings",
                    "content": "Learn how to reduce your tax liability...",
                    "approach": "problem_solution",
                    "hashtags": ["#tax", "#business", "#audit"],
                    "cta": "DM for details"
                },
                {
                    "title": "Transform Your Finances",
                    "content": "A business owner saved $50K with this...",
                    "approach": "storytelling",
                    "hashtags": ["#success", "#audit", "#finance"],
                    "cta": "Link in bio"
                },
                {
                    "title": "Unlock Compliance",
                    "content": "✓ DIAN compliant ✓ Audit ready ✓ Risk-free",
                    "approach": "value_first",
                    "hashtags": ["#compliance", "#dian", "#audit"],
                    "cta": "Book now"
                }
            ]
        }):
            result = self.agent.execute(input_data)

            assert "campaign_id" in result
            assert "channel" in result
            assert "variations" in result
            assert len(result["variations"]) == 3
            assert result["total_variations"] == 3
            assert result["channel"] == "instagram"

    def test_generate_variations_with_llm(self):
        """Test that LLM is called for variation generation"""
        campaign = {"objective": "awareness"}
        tax_dna = {
            "verbal_identity": {"tone": "Casual", "key_phrases": ["tax", "easy"]},
            "servicios": {"primary_services": []},
            "buyer_personas": []
        }
        channel = "instagram"
        tone = "Casual"
        count = 2

        mock_response = {
            "variations": [
                {
                    "title": "Easy Tax Tips",
                    "content": "Here are 3 ways to simplify taxes...",
                    "approach": "educational",
                    "hashtags": ["#tax", "#tips"],
                    "cta": "Follow for more"
                },
                {
                    "title": "Tax Made Simple",
                    "content": "We make taxes fun and easy...",
                    "approach": "value_first",
                    "hashtags": ["#tax", "#easy"],
                    "cta": "DM us"
                }
            ]
        }

        with patch.object(self.agent, 'call_llm', return_value=mock_response) as mock_llm:
            variations = self.agent._generate_variations(campaign, tax_dna, channel, tone, count)

            # Verify LLM was called
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            assert "response_format" in call_args.kwargs
            assert call_args.kwargs["response_format"] == "json"

            # Verify variations returned
            assert len(variations) == count
            assert all("variation_id" in v for v in variations)
            assert all("titulo" in v for v in variations)
            assert all("contenido" in v for v in variations)

    def test_generate_variations_fallback_on_llm_error(self):
        """Test fallback when LLM generation fails"""
        campaign = {"objective": "lead_gen"}
        tax_dna = {
            "verbal_identity": {"tone": "Professional"},
            "servicios": {"primary_services": [{"name": "Audit"}]},
            "buyer_personas": [{"name": "CFO"}]
        }
        channel = "linkedin"
        tone = "Professional"
        count = 2

        # Mock LLM returning parsing error
        with patch.object(self.agent, 'call_llm', return_value={
            "parsing_error": True
        }):
            variations = self.agent._generate_variations(campaign, tax_dna, channel, tone, count)

            # Should return fallback variations
            assert len(variations) == count
            assert all("variation_id" in v for v in variations)
            assert all("note" in v and "Fallback" in v["note"] for v in variations)

    def test_generate_variations_with_different_channels(self):
        """Test variation generation respects channel context"""
        campaign = {"objective": "awareness"}
        tax_dna = {
            "verbal_identity": {"tone": "Professional"},
            "servicios": {"primary_services": []},
            "buyer_personas": []
        }
        count = 1

        # Test Instagram variations
        with patch.object(self.agent, 'call_llm', return_value={
            "variations": [{
                "title": "Instagram Title",
                "content": "Instagram content here",
                "approach": "social",
                "hashtags": ["#ig", "#business"],
                "cta": "DM us"
            }]
        }):
            ig_variations = self.agent._generate_variations(campaign, tax_dna, "instagram", "professional", count)
            assert ig_variations[0]["channel"] == "instagram"

        # Test LinkedIn variations
        with patch.object(self.agent, 'call_llm', return_value={
            "variations": [{
                "title": "LinkedIn Insight",
                "content": "Professional content for linkedin",
                "approach": "thought_leadership",
                "hashtags": ["#linkedin", "#business"],
                "cta": "Connect with me"
            }]
        }):
            li_variations = self.agent._generate_variations(campaign, tax_dna, "linkedin", "professional", count)
            assert li_variations[0]["channel"] == "linkedin"

    def test_add_compliance_checks(self):
        """Test compliance checking on variations"""
        variations = [
            {
                "titulo": "Guaranteed Results",
                "contenido": "100% guaranteed tax savings"
            },
            {
                "titulo": "Professional Audit",
                "contenido": "Expert-led compliance audit"
            }
        ]

        tax_dna = {
            "compliance_rules": {
                "forbidden_claims": ["Guaranteed results", "No risk"],
                "required_disclaimers": ["Subject to individual circumstances"]
            }
        }

        result = self.agent._add_compliance(variations, tax_dna)

        # First variation should have warning (contains "Guaranteed")
        assert result[0].get("compliance_warning") is not None
        assert result[0]["compliance_checked"] is False

        # Second variation should be compliant
        assert result[1].get("compliance_warning") is None
        assert result[1]["compliance_checked"] is True

    def test_optimize_for_channel_instagram(self):
        """Test Instagram-specific optimization"""
        content = {
            "titulo": "Test Title",
            "contenido": "This is a very long piece of content that should be truncated for Instagram to fit within character limits"
        }

        result = self.agent.optimize_for_channel(content, "instagram")

        assert result["format"] == "carousel"
        assert len(result["contenido"]) <= 300

    def test_optimize_for_channel_tiktok(self):
        """Test TikTok-specific optimization"""
        content = {
            "titulo": "Test Title",
            "contenido": "This is a long piece of content that should be very short for TikTok format"
        }

        result = self.agent.optimize_for_channel(content, "tiktok")

        assert result["format"] == "short_video"
        assert len(result["contenido"]) <= 150

    def test_optimize_for_channel_linkedin(self):
        """Test LinkedIn-specific optimization"""
        content = {
            "titulo": "Professional Insight",
            "contenido": "This is a professional article for LinkedIn that can be longer and more detailed to engage professionals"
        }

        result = self.agent.optimize_for_channel(content, "linkedin")

        assert result["format"] == "article"
        assert len(result["contenido"]) <= 500

    def test_optimize_for_channel_email(self):
        """Test Email-specific optimization"""
        content = {
            "titulo": "Special Offer",
            "contenido": "Don't miss this limited time offer"
        }

        result = self.agent.optimize_for_channel(content, "email")

        assert result["format"] == "email"
        assert "subject" in result
        assert result["subject"] == content["titulo"]

    def test_get_channel_templates(self):
        """Test template retrieval for different channels"""
        tax_dna = {}

        instagram_templates = self.agent._get_channel_templates("instagram", tax_dna)
        assert "problem_solution" in instagram_templates
        assert "story_arc" in instagram_templates

        linkedin_templates = self.agent._get_channel_templates("linkedin", tax_dna)
        assert "thought_leadership" in linkedin_templates
        assert "case_study" in linkedin_templates

        tiktok_templates = self.agent._get_channel_templates("tiktok", tax_dna)
        assert "trend_based" in tiktok_templates
        assert "quick_tip" in tiktok_templates

    def test_select_emoji(self):
        """Test emoji selection per channel"""
        campaign = {}

        instagram_emoji = self.agent._select_emoji(campaign, "instagram")
        assert instagram_emoji == "📸"

        linkedin_emoji = self.agent._select_emoji(campaign, "linkedin")
        assert linkedin_emoji == "💼"

        tiktok_emoji = self.agent._select_emoji(campaign, "tiktok")
        assert tiktok_emoji == "🎬"

    def test_generate_cta(self):
        """Test CTA generation per channel"""
        campaign = {}

        instagram_cta = self.agent._generate_cta(campaign, "instagram", 0)
        assert isinstance(instagram_cta, str)
        assert len(instagram_cta) > 0

        linkedin_cta = self.agent._generate_cta(campaign, "linkedin", 0)
        assert isinstance(linkedin_cta, str)
        assert "Comment" in linkedin_cta or "Connect" in linkedin_cta


class TestGeneratorAgentIntegration:
    """Integration tests for GeneratorAgent"""

    def test_full_content_generation_flow(self):
        """Test complete content generation flow for campaign"""
        agent = GeneratorAgent()

        input_data = {
            "campaign": {
                "id": "camp-001",
                "objective": "lead_generation",
                "name": "Q2 Tax Audit Campaign"
            },
            "tax_dna": {
                "verbal_identity": {
                    "tone": "Professional and approachable",
                    "key_phrases": ["tax audit", "compliance", "fiscal planning"]
                },
                "servicios": {
                    "primary_services": [
                        {"name": "Tax Auditing"},
                        {"name": "Fiscal Planning"},
                        {"name": "Compliance Consulting"}
                    ]
                },
                "buyer_personas": [
                    {"name": "Small Business Owner"},
                    {"name": "Finance Manager"}
                ],
                "compliance_rules": {
                    "forbidden_claims": ["Guaranteed savings", "Risk-free"],
                    "required_disclaimers": ["Results vary by situation"]
                }
            },
            "channel": "instagram",
            "tone": "Professional and approachable",
            "variations_count": 3
        }

        with patch.object(agent, 'call_llm', return_value={
            "variations": [
                {
                    "title": "Is Your Tax Audit Ready?",
                    "content": "Most businesses aren't prepared for tax audits. Here's what you need to know...",
                    "approach": "problem_solution",
                    "hashtags": ["#taxaudit", "#compliance", "#business"],
                    "cta": "DM for checklist"
                },
                {
                    "title": "From Chaos to Clarity",
                    "content": "Watch how business owners go from worried to confident in their tax position...",
                    "approach": "storytelling",
                    "hashtags": ["#taxplanning", "#business", "#success"],
                    "cta": "Link in bio"
                },
                {
                    "title": "Complete Audit Preparation",
                    "content": "✓ Document review ✓ Risk assessment ✓ Action plan",
                    "approach": "value_first",
                    "hashtags": ["#audit", "#preparation", "#fiscal"],
                    "cta": "Book consultation"
                }
            ]
        }):
            result = agent.execute(input_data)

            assert result["campaign_id"] == "camp-001"
            assert result["channel"] == "instagram"
            assert result["total_variations"] == 3

            # Verify all variations have required fields
            for variation in result["variations"]:
                assert "variation_id" in variation
                assert "titulo" in variation
                assert "contenido" in variation
                assert "hashtags" in variation
                assert "cta" in variation

    def test_multi_channel_generation(self):
        """Test generating variations for multiple channels"""
        agent = GeneratorAgent()

        base_tax_dna = {
            "verbal_identity": {"tone": "Professional", "key_phrases": ["consulting", "business"]},
            "servicios": {"primary_services": [{"name": "Consulting"}]},
            "buyer_personas": []
        }
        campaign = {"objective": "awareness"}

        channels = ["instagram", "linkedin", "tiktok"]

        for channel in channels:
            with patch.object(agent, 'call_llm', return_value={
                "variations": [{
                    "title": f"{channel.capitalize()} Title",
                    "content": f"Content optimized for {channel}",
                    "approach": "strategic",
                    "hashtags": [f"#{channel}"],
                    "cta": "Learn more"
                }]
            }):
                result = agent._generate_variations(campaign, base_tax_dna, channel, "professional", 1)
                assert result[0]["channel"] == channel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
