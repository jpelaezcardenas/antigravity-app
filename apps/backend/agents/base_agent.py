"""
Base Agent Class - LÍNEA 3
Foundation for all 7 agents in the Social Content Ops system

Aligns with Sight AI 2026 Content Ops model:
1. Discovery (Onboarding) - Extract brand identity and trends
2. SEO/Strategist (Planner) - Generate campaign options with ROI
3. Generator - Create content variations
4. Editor (Legal Reviewer) - Validate compliance and facts
5. Repurposer - Transform content across formats
6. Analyst/Reporting - Monitor metrics and generate insights
7. Distribution - Publish to channels
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Available agent roles - mapped to Sight AI 2026 model"""
    # Core agents (Sight AI roles)
    DISCOVERY = "discovery"           # Brand analysis + trends
    SEO_STRATEGIST = "seo_strategist" # Campaign planning with SEO
    GENERATOR = "generator"           # Content generation
    EDITOR = "editor"                 # Compliance checking + fact-checking
    REPURPOSER = "repurposer"         # Content transformation
    ANALYST = "analyst"               # Metrics + insights
    DISTRIBUTION = "distribution"     # Publishing to channels

    # Legacy aliases for backwards compatibility
    ONBOARDING = "onboarding"         # Alias for DISCOVERY
    PLANNER = "planner"               # Alias for SEO_STRATEGIST
    LEGAL_REVIEWER = "legal_reviewer" # Alias for EDITOR
    IMAGE_GENERATOR = "image_generator"       # Deprecated
    COLLABORATIVE_EDITOR = "collaborative_editor" # Deprecated
    FEEDBACK_ML = "feedback_ml"       # Deprecated


class BaseAgent(ABC):
    """
    Base class for all agents in FASE 2

    All agents follow this pattern:
    1. Receive input (campaign data, content, etc.)
    2. Process using their specialized knowledge
    3. Return structured output
    4. Log interactions for ML feedback
    """

    def __init__(self, role: AgentRole, name: str, version: str = "1.0"):
        """
        Initialize base agent

        Args:
            role: Agent's role in the system
            name: Human-readable agent name
            version: Agent version
        """
        self.role = role
        self.name = name
        self.version = version
        self.created_at = datetime.now().isoformat()
        self.interaction_log: List[Dict] = []
        self.llm_chain = None
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """
        Main execution method - must be implemented by subclasses

        Args:
            input_data: Task-specific input data

        Returns:
            Task-specific output data
        """
        pass

    def process(self, input_data: Dict, context: Optional[Dict] = None) -> Dict:
        """
        Wrapper around execute() that handles logging and error handling

        Args:
            input_data: Task input
            context: Optional context (campaign data, user preferences, etc.)

        Returns:
            Execution result with metadata
        """
        try:
            # Log interaction start
            interaction = {
                "agent": self.name,
                "role": self.role.value,
                "timestamp": datetime.now().isoformat(),
                "input": input_data,
                "context": context
            }

            # Execute the agent's logic
            output = self.execute(input_data)

            # Log interaction result
            interaction["output"] = output
            interaction["status"] = "success"
            self.interaction_log.append(interaction)

            return {
                "status": "success",
                "agent": self.name,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Log error
            interaction["error"] = str(e)
            interaction["status"] = "failed"
            self.interaction_log.append(interaction)

            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def validate_input(self, input_data: Dict, required_fields: List[str]) -> bool:
        """
        Validate that input has required fields

        Args:
            input_data: Input to validate
            required_fields: List of required field names

        Returns:
            True if valid, False otherwise
        """
        for field in required_fields:
            if field not in input_data:
                return False
        return True

    def set_llm_chain(self, llm_chain):
        """Set the LLM chain for this agent (Groq -> Cerebras -> Mistral)"""
        self.llm_chain = llm_chain

    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: str = "text",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> Union[Dict, str, Any]:
        """
        Call LLM with automatic failover and JSON auto-healing.

        Uses llm_engine.py with Groq → Cerebras → Mistral → Gemini → OpenRouter.

        Args:
            prompt: User prompt/query
            system_prompt: Optional system context (defaults to agent name)
            response_format: "json" or "text"
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0-1)
            **kwargs: Additional arguments passed to LLM engine

        Returns:
            Dict if response_format="json", str if response_format="text"
        """
        try:
            from agents.llm_engine import get_ai_response
        except ImportError:
            logger.error("llm_engine module not found")
            return {} if response_format == "json" else ""

        try:
            default_system = f"You are a {self.name} agent for Contexia helping with {self.role.value} tasks."
            final_system_prompt = system_prompt or default_system

            logger.debug(f"{self.name} calling LLM with format={response_format}")

            response = get_ai_response(
                prompt=prompt,
                system_prompt=final_system_prompt,
                response_format=response_format,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            logger.debug(f"{self.name} received LLM response")
            return response

        except Exception as e:
            logger.error(f"LLM error in {self.name}: {str(e)}")
            return {} if response_format == "json" else ""

    def get_interaction_log(self) -> List[Dict]:
        """Get all interactions for this agent"""
        return self.interaction_log

    def clear_interaction_log(self):
        """Clear interaction history"""
        self.interaction_log = []

    def get_stats(self) -> Dict:
        """Get agent statistics"""
        successful = sum(1 for i in self.interaction_log if i.get("status") == "success")
        failed = sum(1 for i in self.interaction_log if i.get("status") == "failed")
        total = len(self.interaction_log)

        return {
            "agent": self.name,
            "role": self.role.value,
            "total_interactions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "created_at": self.created_at
        }

    def __repr__(self) -> str:
        return f"<{self.name} v{self.version} ({self.role.value})>"


class AgentInput:
    """Base class for agent input validation"""

    @staticmethod
    def validate_campaign_id(campaign_id: str) -> bool:
        """Check if campaign ID is valid"""
        return campaign_id and len(campaign_id) > 0

    @staticmethod
    def validate_content(content: str) -> bool:
        """Check if content is valid"""
        return content and len(content.strip()) > 0

    @staticmethod
    def validate_url(url: str) -> bool:
        """Check if URL is valid"""
        return url and (url.startswith("http://") or url.startswith("https://"))


class AgentOutput:
    """Base class for standardizing agent output"""

    @staticmethod
    def success(data: Dict, agent_name: str) -> Dict:
        """Format successful output"""
        return {
            "status": "success",
            "agent": agent_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def error(error: str, agent_name: str) -> Dict:
        """Format error output"""
        return {
            "status": "error",
            "agent": agent_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def partial(data: Dict, agent_name: str, issues: List[str] = None) -> Dict:
        """Format partial/incomplete output"""
        return {
            "status": "partial",
            "agent": agent_name,
            "data": data,
            "issues": issues or [],
            "timestamp": datetime.now().isoformat()
        }
