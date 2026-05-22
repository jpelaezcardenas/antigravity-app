"""
Model Selector: Automatically decide which LLM provider to use based on task type.

Strategy (Cloud-Only):
- TIER 1 (Free, Non-Sensitive): OpenRouter Free (FAQ, social, general)
- TIER 2 (Free, Financial): OpenRouter Free (Pulso, Centinela monitoring) with Groq fallback
- TIER 3 (Critical, Fiscal): Groq (Compliance, fiscal decisions)
"""

from enum import Enum
from agents.llm_engine import LLMProvider


class TaskType(Enum):
    """Task categories for automatic model selection"""
    # Tier 1: Non-sensitive, simple tasks
    TATY_FAQ = "taty_faq"
    DATA_EXTRACTION = "data_extraction"
    SOCIAL_CONTENT_GEN = "social_content_gen"
    SOCIAL_ANALYSIS = "social_analysis"
    GENERAL_INQUIRY = "general_inquiry"

    # Tier 2: Financial data, private
    PULSO_ANALYSIS = "pulso_analysis"
    CENTINELA_MONITORING = "centinela_monitoring"

    # Tier 3: Critical, fiscal/compliance
    CENTINELA_DECISION = "centinela_decision"
    COMPLIANCE_AUDIT = "compliance_audit"
    FISCAL_STRATEGY = "fiscal_strategy"


def choose_model_for_task(task_type: str) -> LLMProvider:
    """
    Decide which LLM provider to use based on task type.

    This function transparently routes requests to optimize:
    1. Cost (prefer free models)
    2. Privacy (keep financial data local)
    3. Reliability (use paid for critical decisions)

    User NEVER knows which model is used - completely transparent.

    Args:
        task_type: Task identifier (from TaskType enum or string)

    Returns:
        LLMProvider to use for this task
    """

    # Normalize task_type to string
    if isinstance(task_type, TaskType):
        task_type = task_type.value

    task_type = task_type.lower().strip()

    # ============================================
    # TIER 1: OpenRouter Free (Non-sensitive)
    # ============================================
    if task_type in [
        "taty_faq",
        "taty_faq_lookup",
        "faq",
        "data_extraction",
        "extract_data",
        "social_content_gen",
        "social_content_generation",
        "social_analysis",
        "general_inquiry",
        "ask_question",
    ]:
        return LLMProvider.OPENROUTER_FREE

    # ============================================
    # TIER 2: OpenRouter Free (Financial, free cloud)
    # Note: Fallback to Groq if rate-limited
    # ============================================
    if task_type in [
        "pulso_analysis",
        "pulso_analyze",
        "pulso",
        "centinela_monitoring",
        "centinela_monitor",
        "centinela_check",
        "transaction_review",
        "cash_flow_analysis",
    ]:
        return LLMProvider.OPENROUTER_FREE

    # ============================================
    # TIER 3: Groq (Critical, fiscal/compliance)
    # ============================================
    if task_type in [
        "centinela_decision",
        "centinela_fiscal_decision",
        "compliance_audit",
        "fiscal_strategy",
        "tax_planning",
        "legal_review",
        "regulatory_check",
        "dian_review",
    ]:
        return LLMProvider.GROQ

    # ============================================
    # DEFAULT: Fallback to Groq (safest option)
    # ============================================
    return LLMProvider.GROQ


def get_task_tier(task_type: str) -> str:
    """
    Get the tier (criticality level) of a task.

    Returns: "tier_1", "tier_2", or "tier_3"
    """
    task_type = task_type.lower().strip()

    # Tier 1: Non-sensitive data
    if task_type in ["taty_faq", "taty_faq_lookup", "faq", "data_extraction",
                      "extract_data", "social_content_gen", "social_content_generation",
                      "social_analysis", "general_inquiry", "ask_question"]:
        return "tier_1"

    # Tier 2: Financial data (free cloud)
    if task_type in ["pulso_analysis", "pulso_analyze", "pulso",
                      "centinela_monitoring", "centinela_monitor", "centinela_check",
                      "transaction_review", "cash_flow_analysis"]:
        return "tier_2"

    # Tier 3: Critical fiscal/compliance (always Groq)
    if task_type in ["centinela_decision", "centinela_fiscal_decision",
                      "compliance_audit", "fiscal_strategy", "tax_planning",
                      "legal_review", "regulatory_check", "dian_review"]:
        return "tier_3"

    # Default to Tier 3 (safest)
    return "tier_3"


def get_task_description(task_type: str) -> dict:
    """
    Get detailed information about a task and its model selection.

    Useful for logging, debugging, and understanding cost optimization.
    """
    model = choose_model_for_task(task_type)
    tier = get_task_tier(task_type)

    tier_info = {
        "tier_1": {
            "name": "Non-Sensitive (Free)",
            "model": "OpenRouter Free",
            "privacy": "Data sent to OpenRouter cloud",
            "cost": "$0 (free tier)",
            "examples": "FAQ, social media, general queries"
        },
        "tier_2": {
            "name": "Financial (Free Cloud)",
            "model": "OpenRouter Free",
            "privacy": "Data sent to OpenRouter cloud (acceptable for financial analysis)",
            "cost": "$0 (free tier, ~100 req/day)",
            "examples": "Pulso analysis, Centinela monitoring"
        },
        "tier_3": {
            "name": "Critical (Paid)",
            "model": "Groq",
            "privacy": "Encrypted in transit, no retention",
            "cost": "$0.20/call (guaranteed quality)",
            "examples": "Fiscal decisions, compliance audits"
        }
    }

    return {
        "task_type": task_type,
        "tier": tier,
        "provider": model.value,
        "details": tier_info[tier]
    }


# Examples of task routing (for documentation)
ROUTING_EXAMPLES = {
    "taty_faq": {
        "description": "User asking FAQ about taxes",
        "model": "OpenRouter Free",
        "reason": "Non-sensitive, no personal data"
    },
    "pulso_analysis": {
        "description": "Analyze user's daily cash flow",
        "model": "OpenRouter Free",
        "reason": "Financial data, free cloud OK, fallback Groq if rate-limited"
    },
    "centinela_monitoring": {
        "description": "Check fiscal threshold status",
        "model": "OpenRouter Free",
        "reason": "Financial monitoring, free cloud stable, fallback Groq if needed"
    },
    "centinela_decision": {
        "description": "Recommend if user should file tax return",
        "model": "Groq",
        "reason": "Critical fiscal decision, need reliability"
    },
    "compliance_audit": {
        "description": "Audit user compliance with DIAN rules",
        "model": "Groq",
        "reason": "Regulatory/legal, non-negotiable quality"
    }
}
