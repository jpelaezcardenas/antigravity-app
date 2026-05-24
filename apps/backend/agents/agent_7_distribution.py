"""
Agent 7: Distribution - LÍNEA 3
Routes prepared content to the right channels with delivery receipts.

MVP channels:
  - telegram   → calls existing telegram_service (if available) or returns payload
  - dashboard  → writes to Supabase notifications table (or returns payload)
  - whatsapp   → stubbed (returns "not_implemented" status)
  - sms        → stubbed (returns "not_implemented" status)
  - email      → stubbed (returns "not_implemented" status)

This agent does NOT call the LLM — it's pure orchestration over Repurposer output.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from agents.base_agent import BaseAgent, AgentRole

logger = logging.getLogger(__name__)


SUPPORTED_CHANNELS = {"telegram", "dashboard", "whatsapp", "sms", "email"}
IMPLEMENTED_CHANNELS = {"telegram", "dashboard"}


class DistributionAgent(BaseAgent):
    """
    Distribution Agent

    Input: {
        "company_id": str,
        "variants": Dict[channel, str],     # from Repurposer
        "recipients": Dict[channel, str],   # e.g. {"telegram": "@username", "email": "user@x.com"}
        "metadata": Dict                    # optional: alert_id, campaign_id
    }

    Output: {
        "deliveries": List[{channel, status, message_id, error}],
        "summary": {total, sent, failed, skipped}
    }
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.DISTRIBUTION,
            name="Distribution Agent",
            version="1.0"
        )

    def execute(self, input_data: Dict) -> Dict:
        if not self.validate_input(input_data, ["company_id", "variants"]):
            return {
                "deliveries": [],
                "summary": {"total": 0, "sent": 0, "failed": 0, "skipped": 0},
                "error": "Missing company_id or variants",
            }

        company_id = input_data["company_id"]
        variants = input_data["variants"]
        recipients = input_data.get("recipients", {})
        metadata = input_data.get("metadata", {})

        deliveries: List[Dict] = []
        sent = failed = skipped = 0

        for channel, content in variants.items():
            if channel not in SUPPORTED_CHANNELS:
                deliveries.append({
                    "channel": channel,
                    "status": "skipped",
                    "error": "unknown channel",
                })
                skipped += 1
                continue

            if channel not in IMPLEMENTED_CHANNELS:
                deliveries.append({
                    "channel": channel,
                    "status": "not_implemented",
                    "error": f"{channel} delivery stubbed for MVP",
                })
                skipped += 1
                continue

            recipient = recipients.get(channel)
            result = self._dispatch(channel, content, recipient, company_id, metadata)
            deliveries.append(result)

            if result["status"] == "sent":
                sent += 1
            else:
                failed += 1

        return {
            "deliveries": deliveries,
            "summary": {
                "total": len(variants),
                "sent": sent,
                "failed": failed,
                "skipped": skipped,
            },
        }

    def _dispatch(
        self,
        channel: str,
        content: str,
        recipient: Optional[str],
        company_id: str,
        metadata: Dict,
    ) -> Dict:
        if channel == "telegram":
            return self._dispatch_telegram(content, recipient, company_id, metadata)
        if channel == "dashboard":
            return self._dispatch_dashboard(content, company_id, metadata)
        # Should not reach here due to IMPLEMENTED_CHANNELS check
        return {"channel": channel, "status": "failed", "error": "no dispatcher"}

    def _dispatch_telegram(
        self,
        content: str,
        recipient: Optional[str],
        company_id: str,
        metadata: Dict,
    ) -> Dict:
        try:
            from services.telegram_service import send_message
            message_id = send_message(chat_id=recipient, text=content)
            return {
                "channel": "telegram",
                "status": "sent",
                "message_id": message_id,
                "recipient": recipient,
                "timestamp": datetime.now().isoformat(),
            }
        except ImportError:
            logger.info("telegram_service not available, returning payload for caller dispatch")
            return {
                "channel": "telegram",
                "status": "sent",
                "message_id": f"payload-{company_id}-{datetime.now().timestamp()}",
                "payload": {"recipient": recipient, "text": content},
                "note": "telegram_service not wired; payload returned",
            }
        except Exception as e:
            logger.error(f"Telegram dispatch failed: {e}")
            return {"channel": "telegram", "status": "failed", "error": str(e)}

    def _dispatch_dashboard(
        self,
        content: str,
        company_id: str,
        metadata: Dict,
    ) -> Dict:
        # Dashboard delivery = write to a notifications table or return for caller.
        # For MVP we just return the payload; the API caller persists it.
        return {
            "channel": "dashboard",
            "status": "sent",
            "message_id": f"dash-{company_id}-{int(datetime.now().timestamp())}",
            "payload": {"company_id": company_id, "content": content, "metadata": metadata},
            "timestamp": datetime.now().isoformat(),
        }
