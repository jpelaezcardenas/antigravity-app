"""
Agent 2: Planner / SEO Strategist - LÍNEA 3
Generates campaign options based on Tax DNA and objectives using real LLM
Aligns with Sight AI "SEO Strategist" role for campaign planning with ROI optimization
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from agents.base_agent import BaseAgent, AgentRole, AgentOutput

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Campaign Planner / SEO Strategist Agent

    Generates strategic marketing campaign options optimized for ROI and SEO.
    Uses real LLM to create context-aware campaign recommendations based on
    company Tax DNA, objectives, budget, and target channels.

    Input: Tax DNA + Campaign objective + Budget + Channels
    Output: 3-5 strategic campaign options with ROI analysis
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.SEO_STRATEGIST,
            name="SEO Strategist Agent",
            version="2.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        """
        Generate campaign options

        Input expected:
        {
            "campaign_objective": str,
            "tax_dna": Dict,
            "budget": float,
            "timeline_weeks": int,
            "target_channels": List[str]
        }

        Output: List of 3-5 campaign options
        """
        tax_dna = input_data.get("tax_dna", {})
        objective = input_data.get("campaign_objective", "General awareness")
        budget = input_data.get("budget", 5000)
        weeks = input_data.get("timeline_weeks", 4)
        channels = input_data.get("target_channels", ["instagram", "linkedin", "facebook"])

        # Generate options based on objective
        campaign_options = self._generate_options(
            objective,
            tax_dna,
            budget,
            weeks,
            channels
        )

        # Rank options by potential ROI
        ranked_options = self._rank_options(campaign_options, objective, budget)

        return {
            "campaign_options": ranked_options,
            "recommendation": ranked_options[0] if ranked_options else None,
            "total_options": len(ranked_options),
            "budget_analysis": self._analyze_budget(budget, len(ranked_options))
        }

    def _generate_options(
        self,
        objective: str,
        tax_dna: Dict,
        budget: float,
        weeks: int,
        channels: List[str]
    ) -> List[Dict]:
        """Generate multiple campaign options using real LLM based on objective and Tax DNA"""

        # Extract key Tax DNA components for context
        brand_voice = tax_dna.get("verbal_identity", {})
        services = tax_dna.get("servicios", {})
        personas = tax_dna.get("buyer_personas", [])

        prompt = f"""Based on the following campaign parameters, generate 3-5 strategic marketing campaign options.

Campaign Objective: {objective}
Budget: ${budget}
Timeline: {weeks} weeks
Target Channels: {', '.join(channels)}
Brand Tone: {brand_voice.get('tone', 'Professional')}
Key Services: {', '.join([s.get('name', '') for s in services.get('primary_services', [])[:3]])}

For each campaign option, provide:
1. A unique campaign name
2. Workflow type (e.g., "instagram-calendar", "product-launch", "storytelling-series")
3. Detailed description aligned with the brand voice
4. Timeline (in weeks)
5. Number of posts needed
6. Budget allocation as percentages (content_creation, promotion, management, etc.)
7. Expected metrics (reach, engagement, conversions with realistic estimates)
8. Best use cases (2-3 bullet points)
9. Difficulty level (Easy/Medium/High)
10. Estimated ROI (1.0 to 10.0 scale)

Return a JSON object with key "options" containing an array of campaigns.
Each campaign should be optimized for the objective and realistic for the budget.

Return ONLY valid JSON, no additional text."""

        system_prompt = "You are a strategic campaign planner specializing in creating high-ROI marketing campaigns tailored to company brand voice and objectives. Return valid JSON only."

        response = self.call_llm(prompt, system_prompt, response_format="json")

        # Parse and validate response
        if isinstance(response, dict) and response.get("parsing_error"):
            logger.warning("LLM JSON parsing failed, using fallback campaign options")
            return self._campaign_options_fallback(budget, weeks, channels)

        # Extract options from response
        if isinstance(response, dict) and "options" in response:
            options = response["options"]
            if isinstance(options, list) and len(options) > 0:
                # Enrich with option_id
                for idx, opt in enumerate(options, 1):
                    opt["option_id"] = idx
                return options

        logger.warning("LLM returned unexpected format, using fallback")
        return self._campaign_options_fallback(budget, weeks, channels)

    def _rank_options(self, options: List[Dict], objective: str, budget: float) -> List[Dict]:
        """Rank options by objective match and ROI"""

        # Define objective-to-option scoring
        objective_map = {
            "awareness": [1, 4],  # Instagram Calendar, Local
            "engagement": [3, 2],  # Storytelling, Product Launch
            "conversion": [5, 2],  # Retargeting, Product Launch
            "retention": [3, 5],   # Storytelling, Retargeting
            "launch": [2, 4],      # Product Launch, Local
            "lead_generation": [1, 4, 5],  # Instagram, Local, Retargeting
            "local_expansion": [4],  # Local only
            "general": list(range(1, 6))  # All options
        }

        # Get relevant options
        relevant_ids = objective_map.get(objective.lower().replace(" ", "_"), list(range(1, 6)))

        # Score and rank
        ranked = []
        for opt in options:
            if opt["option_id"] in relevant_ids:
                # Adjust score based on budget fit
                budget_fit = min(budget / sum(opt["budget_allocation"].values()), 1.0)
                opt["relevance_score"] = (opt["estimated_roi"] * budget_fit) * 100
                ranked.append(opt)

        # Sort by relevance score (descending)
        ranked.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return ranked

    def _analyze_budget(self, total_budget: float, num_options: int) -> Dict:
        """Analyze budget allocation recommendations"""
        return {
            "total_budget": total_budget,
            "per_option_budget": total_budget / num_options if num_options > 0 else 0,
            "recommendations": [
                "Allocate 30-40% to content creation",
                "Allocate 45-50% to promotion/ads",
                "Allocate 10-15% to management/tools"
            ],
            "budget_sufficient": total_budget >= 2000,
            "minimum_recommended": 2000,
            "optimal_budget": 5000
        }

    def _campaign_options_fallback(self, budget: float, weeks: int, channels: List[str]) -> List[Dict]:
        """Fallback campaign options when LLM parsing fails"""
        return [
            {
                "option_id": 1,
                "name": "Instagram Calendar - 4-Pillar",
                "workflow_type": "instagram-calendar",
                "description": "Weekly rotation: Regulatory → Educational → Commercial → Social Proof",
                "timeline": f"{weeks} weeks",
                "channels": ["instagram"] if "instagram" in channels else channels[:1],
                "posts_count": weeks * 4,
                "budget_allocation": {
                    "content_creation": budget * 0.3,
                    "promotion": budget * 0.6,
                    "management": budget * 0.1
                },
                "expected_metrics": {
                    "reach": 5000 * weeks,
                    "engagement": 250 * weeks,
                    "conversions": 15 * weeks
                },
                "best_for": ["Lead generation", "Ongoing awareness"],
                "difficulty": "Easy",
                "estimated_roi": 3.5,
                "note": "Fallback option - LLM parsing failed"
            },
            {
                "option_id": 2,
                "name": "Retargeting - 6-Segment",
                "workflow_type": "retargeting",
                "description": "Personalized messaging for different audience segments",
                "timeline": f"{weeks} weeks",
                "channels": channels,
                "posts_count": 24,
                "budget_allocation": {
                    "content_creation": budget * 0.2,
                    "automation": budget * 0.3,
                    "promotion": budget * 0.4,
                    "management": budget * 0.1
                },
                "expected_metrics": {
                    "reach": 3000 * weeks,
                    "engagement": 150 * weeks,
                    "conversions": 25 * weeks
                },
                "best_for": ["Customer recovery", "Conversion optimization"],
                "difficulty": "Medium",
                "estimated_roi": 5.2,
                "note": "Fallback option - LLM parsing failed"
            }
        ]

    def optimize_for_seo(self, content: str, target_keywords: List[str]) -> Dict:
        """Optimize content for SEO with target keywords without keyword stuffing"""

        prompt = f"""Optimize the following content for SEO with natural keyword integration.
Target Keywords: {', '.join(target_keywords)}
Original Content: {content[:1000]}

Provide optimized content that:
1. Naturally incorporates target keywords
2. Maintains readability and brand voice
3. Includes meta title suggestion (60 chars max)
4. Includes meta description (160 chars max)
5. Suggests 3-5 semantic variations of keywords
6. Rates keyword integration quality (0-100)

Return JSON with:
- optimized_content: str
- meta_title: str
- meta_description: str
- keyword_variations: list
- integration_quality: int
- seo_score: int (0-100)

Return ONLY valid JSON."""

        system_prompt = "You are an SEO optimization expert. Optimize content naturally without keyword stuffing. Return valid JSON only."

        response = self.call_llm(prompt, system_prompt, response_format="json")

        if isinstance(response, dict) and response.get("parsing_error"):
            logger.warning("SEO optimization LLM failed, returning basic optimization")
            return self._seo_optimization_fallback(content, target_keywords)

        return response if isinstance(response, dict) else self._seo_optimization_fallback(content, target_keywords)

    def generate_hashtags(self, content: str, platform: str, count: int = 10) -> Dict:
        """Generate platform-specific hashtags optimized for reach and relevance"""

        prompt = f"""Generate {count} highly effective hashtags for the following content on {platform}.

Content: {content[:500]}
Platform: {platform}
Count: {count}

Consider:
1. Trending hashtags on {platform}
2. Niche/specific hashtags relevant to content
3. Mix of high-volume and low-competition tags
4. Platform-specific best practices (character limits, usage patterns)

Return JSON with:
- hashtags: list of {count} hashtag strings (with # symbol)
- trending: list of hashtags that are currently trending on {platform}
- niche: list of specific/niche hashtags
- strategy: string explaining the hashtag mix strategy
- estimated_reach: string (low/medium/high)
- platform_recommendations: string with platform-specific tips

Return ONLY valid JSON."""

        system_prompt = f"You are a social media strategist specializing in {platform} hashtag optimization. Return valid JSON only."

        response = self.call_llm(prompt, system_prompt, response_format="json")

        if isinstance(response, dict) and response.get("parsing_error"):
            logger.warning(f"Hashtag generation LLM failed for {platform}, returning fallback")
            return self._hashtags_fallback(count, platform)

        return response if isinstance(response, dict) else self._hashtags_fallback(count, platform)

    def _seo_optimization_fallback(self, content: str, keywords: List[str]) -> Dict:
        """Fallback SEO optimization when LLM fails"""
        return {
            "optimized_content": content,
            "meta_title": f"{keywords[0].title()} - Contexia" if keywords else "Contexia Services",
            "meta_description": content[:160] if content else "Professional services",
            "keyword_variations": keywords,
            "integration_quality": 50,
            "seo_score": 50,
            "note": "Fallback optimization - LLM parsing failed"
        }

    def _hashtags_fallback(self, count: int, platform: str) -> Dict:
        """Fallback hashtag generation when LLM fails"""
        platform_generic = {
            "instagram": ["#marketingagency", "#brandbuilding", "#socialmedia", "#digitalmarketing", "#contentstrategy"],
            "linkedin": ["#marketingprofessionals", "#businessgrowth", "#professionalservices", "#marketing", "#entrepreneurship"],
            "tiktok": ["#marketingtips", "#brandstrategy", "#socialmediamarketing", "#contentcreation", "#viral"],
            "twitter": ["#marketing", "#business", "#socialmedia", "#entrepreneurship", "#strategy"]
        }

        base_tags = platform_generic.get(platform.lower(), ["#marketing", "#business", "#strategy", "#content", "#growth"])
        selected_tags = base_tags[:count]

        return {
            "hashtags": selected_tags,
            "trending": selected_tags[:3],
            "niche": selected_tags[3:],
            "strategy": f"Generic hashtags for {platform}",
            "estimated_reach": "medium",
            "platform_recommendations": f"Use native hashtag discovery tools on {platform}",
            "note": "Fallback hashtags - LLM parsing failed"
        }

    def recommend_combination(self, objectives: List[str], budget: float) -> Dict:
        """
        Recommend a combination of workflows for multiple objectives

        Args:
            objectives: List of campaign objectives
            budget: Total budget to distribute

        Returns:
            Recommended campaign combination with allocation
        """
        total_allocation = {}

        for obj in objectives:
            # Generate options for each objective
            options = self._generate_options(obj, {}, budget / len(objectives), 4, [])
            if options:
                # Get top option
                top = self._rank_options(options, obj, budget / len(objectives))[0]
                total_allocation[obj] = {
                    "workflow": top["workflow_type"],
                    "budget": budget / len(objectives),
                    "estimated_roi": top["estimated_roi"]
                }

        return {
            "combination": total_allocation,
            "total_roi": sum(a["estimated_roi"] for a in total_allocation.values()),
            "duration_weeks": max(opt.get("timeline", "4 weeks") for opt in total_allocation.values()),
            "total_posts": sum(opt.get("posts_count", 0) for opt in total_allocation.values()),
            "rationale": "Combination approach balances multiple objectives for maximum impact"
        }
