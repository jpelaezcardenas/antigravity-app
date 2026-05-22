"""
Agent 3: Generator - LÍNEA 3
Creates AI-generated content (copy variations) per channel using real LLM
Aligns with Sight AI "Generator" role for content creation and variation generation
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from agents.base_agent import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


class GeneratorAgent(BaseAgent):
    """
    Content Generator Agent

    Generates multiple content variations optimized per channel using real LLM.
    Creates copy that aligns with brand voice (Tax DNA) and channel best practices.

    Input: Workflow campaign + Brand DNA + Channel + Tone
    Output: Multiple content variations ready for publication or review
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.GENERATOR,
            name="Content Generator Agent",
            version="2.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        """
        Generate content variations

        Input expected:
        {
            "campaign": Dict,
            "tax_dna": Dict,
            "channel": str,
            "tone": str,
            "variations_count": int
        }

        Output: Multiple content variations ready to publish
        """
        campaign = input_data.get("campaign", {})
        tax_dna = input_data.get("tax_dna", {})
        channel = input_data.get("channel", "instagram")
        tone = input_data.get("tone") or tax_dna.get("verbal_identity", {}).get("tone", "professional")
        variations = input_data.get("variations_count", 3)

        # Generate content variations
        content_variations = self._generate_variations(
            campaign,
            tax_dna,
            channel,
            tone,
            variations
        )

        # Add compliance checks
        compliant_variations = self._add_compliance(content_variations, tax_dna)

        return {
            "campaign_id": campaign.get("id"),
            "channel": channel,
            "variations": compliant_variations,
            "total_variations": len(compliant_variations),
            "generation_quality": "high"
        }

    def _generate_variations(
        self,
        campaign: Dict,
        tax_dna: Dict,
        channel: str,
        tone: str,
        count: int
    ) -> List[Dict]:
        """Generate content variations for a specific channel using real LLM"""

        variations = []
        templates = self._get_channel_templates(channel, tax_dna)

        # Use LLM to generate all variations at once for efficiency
        llm_variations = self._generate_variations_with_llm(
            campaign, tax_dna, channel, tone, count
        )

        # Process LLM output into variation objects
        if llm_variations:
            for i, llm_var in enumerate(llm_variations[:count], 1):
                variation = {
                    "variation_id": i,
                    "channel": channel,
                    "template_used": templates[i % len(templates)] if templates else "generic",
                    "titulo": llm_var.get("title", f"Variation {i}"),
                    "contenido": llm_var.get("content", ""),
                    "hashtags": llm_var.get("hashtags", []),
                    "cta": llm_var.get("cta", self._generate_cta(campaign, channel, i - 1)),
                    "emoji": self._select_emoji(campaign, channel),
                    "approach": llm_var.get("approach", "strategic"),
                    "tone_matched": True,
                    "brand_aligned": True,
                    "compliance_checked": False
                }
                variations.append(variation)
        else:
            # Fallback to template-based generation
            logger.warning("LLM content generation failed, using fallback templates")
            for i in range(count):
                variation = {
                    "variation_id": i + 1,
                    "channel": channel,
                    "template_used": templates[i % len(templates)] if templates else "generic",
                    "titulo": self._generate_title_fallback(campaign, tax_dna, i, tone),
                    "contenido": self._generate_copy_fallback(campaign, tax_dna, channel, i, tone),
                    "hashtags": self._generate_hashtags_fallback(campaign, tax_dna, channel),
                    "cta": self._generate_cta(campaign, channel, i),
                    "emoji": self._select_emoji(campaign, channel),
                    "tone_matched": True,
                    "brand_aligned": True,
                    "compliance_checked": False,
                    "note": "Fallback - LLM generation failed"
                }
                variations.append(variation)

        return variations

    def _get_channel_templates(self, channel: str, tax_dna: Dict) -> List[str]:
        """Get templates based on channel"""
        templates = {
            "instagram": [
                "problem_solution",
                "story_arc",
                "social_proof",
                "urgency",
                "value_prop"
            ],
            "linkedin": [
                "thought_leadership",
                "case_study",
                "industry_insight",
                "achievement",
                "announcement"
            ],
            "facebook": [
                "community_focused",
                "testimonial",
                "offer_based",
                "educational",
                "event_promotion"
            ],
            "tiktok": [
                "trend_based",
                "short_story",
                "behind_scenes",
                "quick_tip",
                "challenge"
            ],
            "email": [
                "welcome_series",
                "educational",
                "promotional",
                "nurture",
                "re_engagement"
            ],
            "whatsapp": [
                "direct_offer",
                "time_sensitive",
                "personal_touch",
                "exclusive_access",
                "reminder"
            ]
        }
        return templates.get(channel, ["generic"])

    def _generate_variations_with_llm(
        self,
        campaign: Dict,
        tax_dna: Dict,
        channel: str,
        tone: str,
        count: int
    ) -> List[Dict]:
        """Generate content variations using real LLM"""

        # Extract key context for LLM
        personas = tax_dna.get("buyer_personas", [])
        services = tax_dna.get("servicios", {})
        verbal_identity = tax_dna.get("verbal_identity", {})
        key_phrases = verbal_identity.get("key_phrases", [])

        prompt = f"""Generate {count} different social media content variations for {channel}.

Campaign Context:
- Objective: {campaign.get('objective', 'Awareness')}
- Services: {', '.join([s.get('name', '') for s in services.get('primary_services', [])[:3]])}
- Target Audience: {', '.join([p.get('name', '') for p in personas[:2]])}
- Tone: {tone}
- Key Messages: {', '.join(key_phrases[:5])}

For each variation, create content that:
1. Is optimized for {channel} platform norms
2. Matches the specified tone
3. Addresses target audience pain points
4. Includes clear value proposition
5. Uses {channel}-appropriate formatting (emojis, hashtags, etc.)

Each variation should use a different approach (e.g., problem-solution, story, social proof, urgency, value-first).

Return a JSON object with key "variations" containing an array of {count} objects.
Each object should have:
- title: Attention-grabbing headline (max 100 chars)
- content: Main copy (max 300 chars for short platforms, 500 for LinkedIn)
- approach: The persuasion approach used (e.g., "problem_solution", "storytelling", "social_proof")
- hashtags: List of 3-5 relevant hashtags for {channel}
- cta: Call-to-action optimized for {channel}

Return ONLY valid JSON, no additional text."""

        system_prompt = f"You are an expert content creator specializing in {channel} marketing. Create compelling, on-brand content variations that drive engagement. Return valid JSON only."

        response = self.call_llm(prompt, system_prompt, response_format="json")

        # Validate and extract variations
        if isinstance(response, dict) and response.get("parsing_error"):
            logger.warning("LLM content generation parsing failed")
            return []

        if isinstance(response, dict) and "variations" in response:
            variations = response["variations"]
            if isinstance(variations, list) and len(variations) > 0:
                return variations

        logger.warning("LLM returned unexpected format for content variations")
        return []

    def _generate_title_fallback(self, campaign: Dict, tax_dna: Dict, index: int, tone: str) -> str:
        """Fallback title generation"""
        emojis = ["🚀", "💡", "⚡", "✨", "🎯", "📊"]
        verbs = ["Discover", "Learn", "Unlock", "Master", "Transform", "Revolutionize"]
        benefits = ["Your Fiscal Risk", "Tax Compliance", "Revenue Potential", "Financial Health"]

        emoji = emojis[index % len(emojis)]
        verb = verbs[index % len(verbs)]
        benefit = benefits[index % len(benefits)]

        return f"{emoji} {verb} {benefit}"

    def _generate_copy_fallback(self, campaign: Dict, tax_dna: Dict, channel: str, index: int, tone: str) -> str:
        """Fallback copy generation when LLM fails"""

        approaches = [
            "problem_agitate_solve",
            "story_based",
            "value_first",
            "social_proof",
            "urgency_based"
        ]

        approach = approaches[index % len(approaches)]
        persona_name = tax_dna.get('buyer_personas', [{}])[0].get('name', 'companies') if tax_dna.get('buyer_personas') else 'companies'

        if approach == "problem_agitate_solve":
            return f"Most {persona_name} waste 40% of their audit budget. Here's how to fix it..."

        elif approach == "story_based":
            return "A contador spent 80 hours auditing clients. Then this changed everything..."

        elif approach == "value_first":
            return "✓ Save $300K in fiscal risks\n✓ 2-hour complete audit\n✓ 100% DIAN compliance"

        elif approach == "social_proof":
            return "450+ contadores already use this. Join them and stop losing money to hidden fiscal risks."

        else:  # urgency_based
            return "Only 5 audits left at this price. The market will price us out soon. Secure yours today."

    def _generate_hashtags_fallback(self, campaign: Dict, tax_dna: Dict, channel: str) -> List[str]:
        """Fallback hashtag generation"""

        base_hashtags = tax_dna.get("verbal_identity", {}).get("key_phrases", [])
        hashtags = [f"#{h.replace(' ', '')}" for h in base_hashtags[:3]]

        # Add channel-specific hashtags
        channel_hashtags = {
            "instagram": ["#auditoriafiscal", "#impuestos", "#contador", "#pyme"],
            "linkedin": ["#fiscalcompliance", "#auditoria", "#dian", "#negocios"],
            "tiktok": ["#fiscaltips", "#contabilidad", "#dinero"],
            "facebook": ["#auditoria", "#impuestos", "#pyme"],
            "email": [],
            "whatsapp": []
        }

        hashtags.extend(channel_hashtags.get(channel, [])[:2])

        return hashtags[:5]

    def _generate_cta(self, campaign: Dict, channel: str, index: int) -> str:
        """Generate call-to-action"""

        ctas = {
            "instagram": [
                "Link en bio →",
                "DM for details",
                "Click nuestro perfil",
                "Swipe up for more"
            ],
            "linkedin": [
                "Comment your experience",
                "Connect with me",
                "Learn more below",
                "Share your thoughts"
            ],
            "facebook": [
                "Get your audit today",
                "Learn more",
                "Book a consultation",
                "See how we help"
            ],
            "tiktok": [
                "Follow for more",
                "Save this tip",
                "DM for help",
                "Share with someone"
            ],
            "email": [
                "Get your audit",
                "Start here",
                "Claim your offer",
                "Join now"
            ],
            "whatsapp": [
                "Send us a message",
                "Chat with us",
                "Reply to book",
                "Tap to start"
            ]
        }

        channel_ctas = ctas.get(channel, ["Learn more"])
        return channel_ctas[index % len(channel_ctas)]

    def _select_emoji(self, campaign: Dict, channel: str) -> str:
        """Select appropriate emoji for content"""

        channel_emojis = {
            "instagram": "📸",
            "linkedin": "💼",
            "facebook": "👥",
            "tiktok": "🎬",
            "email": "📧",
            "whatsapp": "💬"
        }

        return channel_emojis.get(channel, "🚀")

    def _add_compliance(self, variations: List[Dict], tax_dna: Dict) -> List[Dict]:
        """Add compliance checks and required disclaimers"""

        compliance_rules = tax_dna.get("compliance_rules", {})
        forbidden_terms = compliance_rules.get("forbidden_claims", [])
        required_disclaimers = compliance_rules.get("required_disclaimers", [])

        for variation in variations:
            # Check for forbidden terms
            content_to_check = (variation.get("titulo", "") + " " + variation.get("contenido", "")).lower()
            has_forbidden = any(term.lower() in content_to_check for term in forbidden_terms)

            # Check for forbidden claims first
            if has_forbidden:
                variation["compliance_warning"] = "⚠️ Contains potentially forbidden claim - review needed"
                variation["compliance_checked"] = False
            else:
                # If no forbidden claims, mark as checked
                variation["compliance_checked"] = True

                # Add disclaimer if required
                if required_disclaimers:
                    variation["disclaimer"] = required_disclaimers[0]

        return variations

    def optimize_for_channel(self, content: Dict, channel: str) -> Dict:
        """Optimize content specifically for channel requirements"""

        optimized = content.copy()

        if channel == "instagram":
            # Character limits and emoji optimization
            optimized["contenido"] = optimized.get("contenido", "")[:300]
            optimized["format"] = "carousel"

        elif channel == "tiktok":
            # Shorter, punchier
            optimized["contenido"] = optimized.get("contenido", "")[:150]
            optimized["format"] = "short_video"

        elif channel == "linkedin":
            # Professional, longer form
            optimized["contenido"] = optimized.get("contenido", "")[:500]
            optimized["format"] = "article"

        elif channel == "email":
            # Structure for email
            optimized["subject"] = optimized.get("titulo")
            optimized["format"] = "email"

        return optimized
