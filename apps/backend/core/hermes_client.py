"""
Hermes Workspace WebSocket client for approval workflows.

Sends approval requests to Hermes gateway and listens for approval decisions.
Used by Shadow GL HITL pipeline (Phase 6).
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


class HermesClientError(Exception):
    """Raised when Hermes client operation fails."""


class HermesClient:
    """WebSocket client for Hermes approval workflows."""

    def __init__(self, gateway_url: str, token: str, timeout: float = 30.0):
        """
        Initialize Hermes client.

        Args:
            gateway_url: Hermes gateway URL (e.g., http://127.0.0.1:8642)
            token: API token for authentication
            timeout: WebSocket operation timeout in seconds
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.ws = None

    async def connect(self) -> None:
        """Establish WebSocket connection to Hermes gateway."""
        ws_url = self.gateway_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/approvals"

        try:
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    subprotocols=["hermes.approval.v1"],
                    extra_headers={"Authorization": f"Bearer {self.token}"},
                ),
                timeout=self.timeout,
            )
            logger.info(f"Connected to Hermes gateway: {ws_url}")
        except asyncio.TimeoutError as exc:
            logger.error(f"Timeout connecting to Hermes: {ws_url}")
            raise HermesClientError(f"Connection timeout: {exc}") from exc
        except WebSocketException as exc:
            logger.error(f"WebSocket error connecting to Hermes: {exc}")
            raise HermesClientError(f"WebSocket error: {exc}") from exc

    async def send_approval_request(
        self,
        approval_queue_id: str,
        tenant_id: str,
        action_type: str,
        data: Dict[str, Any],
        priority: str = "normal",
    ) -> bool:
        """
        Send approval request to Hermes.

        Args:
            approval_queue_id: approval_queue.id
            tenant_id: Tenant context
            action_type: e.g., "review_accounting_entry"
            data: Approval context (error, raw_input, etc.)
            priority: "normal" or "high"

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.ws:
            await self.connect()

        message = {
            "type": "approval_request",
            "approval_queue_id": approval_queue_id,
            "tenant_id": tenant_id,
            "action_type": action_type,
            "data": data,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        try:
            await asyncio.wait_for(
                self.ws.send(json.dumps(message)),
                timeout=self.timeout,
            )
            logger.info(f"Sent approval_request {approval_queue_id} to Hermes")
            return True
        except Exception as exc:
            logger.error(f"Failed to send approval request: {exc}")
            self.ws = None  # Force reconnect on next attempt
            return False

    async def listen_for_decisions(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for approval_decision messages from Hermes.

        Yields:
            Decision dict from Hermes (status="approved"|"rejected", reason, etc.)
        """
        if not self.ws:
            await self.connect()

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    if data.get("type") == "approval_decision":
                        yield data
                    elif data.get("type") == "error":
                        logger.warning(f"Hermes error: {data.get('message')}")
                except json.JSONDecodeError as exc:
                    logger.error(f"Invalid JSON from Hermes: {exc}")
        except WebSocketException as exc:
            logger.error(f"WebSocket closed: {exc}")
            self.ws = None

    async def send_ack(self, approval_queue_id: str, status: str = "processed") -> None:
        """
        Send ACK back to Hermes after processing decision.

        Args:
            approval_queue_id: approval_queue.id
            status: e.g., "processed"
        """
        if not self.ws:
            logger.warning("WebSocket not connected, skipping ACK")
            return

        ack = {
            "type": "ack",
            "approval_queue_id": approval_queue_id,
            "status": status,
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }

        try:
            await asyncio.wait_for(
                self.ws.send(json.dumps(ack)),
                timeout=self.timeout,
            )
            logger.debug(f"Sent ACK for {approval_queue_id}")
        except Exception as exc:
            logger.warning(f"Failed to send ACK: {exc}")

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            logger.info("Closed Hermes gateway connection")
