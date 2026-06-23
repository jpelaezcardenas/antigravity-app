"""
Transform raw agent output for UI consumption.
Handles currency formatting, date parsing, status mapping, etc.
"""

from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime


class AgentTransformers:
    """Transform raw agent output into UI-ready formats."""

    @staticmethod
    def transform_pulso(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Pulso daily summary for PulsaCard component."""
        return {
            "caja_real": Decimal(str(data.get("cash_on_hand", 0))),
            "dinero_tuyo": Decimal(str(data.get("net_cash", 0))),
            "ventas_ayer": Decimal(str(data.get("yesterday_sales", 0))),
            "salidas_plata": Decimal(str(data.get("outflows", 0))),
            "estado_plata": data.get("status", "neutral"),  # bien/alerta/critico
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
        }

    @staticmethod
    def transform_centinela(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform Centinela alerts for CentinelaAlerts component."""
        return [
            {
                "id": alert.get("id"),
                "type": alert.get("alert_type"),  # iva-due, tax-warning, etc
                "title": alert.get("title"),
                "description": alert.get("description"),
                "urgency": alert.get("urgency", "medium"),  # high/medium/low
                "due_date": alert.get("due_date"),
                "action_label": alert.get("action", "Resolver con Taty"),
            }
            for alert in alerts
        ]

    @staticmethod
    def transform_approval_queue(
        drafts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Transform approval drafts for ApprovalQueue component."""
        return [
            {
                "id": draft.get("id"),
                "type": draft.get("draft_type"),  # email, message, form, etc
                "title": draft.get("title"),
                "description": draft.get("description"),
                "agent": draft.get("agent"),
                "content": draft.get("content"),
                "status": draft.get("status", "pending"),  # pending/approved/rejected
                "created_at": draft.get("created_at"),
            }
            for draft in drafts
        ]

    @staticmethod
    def transform_radar(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Radar predictive risk score."""
        return {
            "risk_score": Decimal(str(data.get("risk_score", 0))),
            "risk_level": data.get("risk_level", "low"),  # low/medium/high/critical
            "factors": data.get("factors", []),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
        }

    @staticmethod
    def transform_social_ops(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Social Ops status."""
        return {
            "status": data.get("status", "idle"),  # idle/processing/paused
            "pending_posts": data.get("pending_posts", 0),
            "scheduled_posts": data.get("scheduled_posts", 0),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
        }

    @staticmethod
    def transform_audit(data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform audit shadow report."""
        return {
            "findings": data.get("findings", []),
            "severity": data.get("severity", "info"),  # info/warning/critical
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
        }
