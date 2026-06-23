"""
Validate and serialize agent output using Pydantic models.
Ensures type safety and catches data format issues early.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator


class PulsaOutput(BaseModel):
    """Validated Pulso agent output."""

    caja_real: Decimal
    dinero_tuyo: Decimal
    ventas_ayer: Decimal
    salidas_plata: Decimal
    estado_plata: str
    timestamp: Optional[str] = None

    @field_validator("estado_plata")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["bien", "alerta", "critico", "neutral"]:
            raise ValueError(f"Invalid status: {v}. Must be bien/alerta/critico/neutral")
        return v

    @field_validator("caja_real", "dinero_tuyo", "ventas_ayer", "salidas_plata", mode="before")
    @classmethod
    def validate_currency(cls, v):
        if v is None:
            return Decimal(0)
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError(f"Invalid currency value: {v}")


class AlertOutput(BaseModel):
    """Validated single alert from Centinela."""

    id: str
    type: str
    title: str
    description: str
    urgency: str
    action_label: Optional[str] = None
    due_date: Optional[str] = None

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        if v not in ["high", "medium", "low"]:
            raise ValueError(f"Invalid urgency: {v}")
        return v


class DraftOutput(BaseModel):
    """Validated draft from approval queue."""

    id: str
    type: str
    title: str
    description: str
    agent: str
    content: dict
    status: str
    created_at: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["pending", "approved", "rejected"]:
            raise ValueError(f"Invalid status: {v}")
        return v


class RiskScoreOutput(BaseModel):
    """Validated Radar risk score output."""

    risk_score: Decimal
    risk_level: str
    factors: List[str] = []
    timestamp: Optional[str] = None

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"Invalid risk level: {v}")
        return v

    @field_validator("risk_score", mode="before")
    @classmethod
    def validate_score(cls, v):
        if v is None:
            return Decimal(0)
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError(f"Invalid risk score: {v}")


class SocialOpsOutput(BaseModel):
    """Validated Social Ops status."""

    status: str
    pending_posts: int = 0
    scheduled_posts: int = 0
    timestamp: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["idle", "processing", "paused", "error"]:
            raise ValueError(f"Invalid status: {v}")
        return v


class AuditOutput(BaseModel):
    """Validated audit findings."""

    findings: List[dict] = []
    severity: str = "info"
    timestamp: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in ["info", "warning", "critical"]:
            raise ValueError(f"Invalid severity: {v}")
        return v
