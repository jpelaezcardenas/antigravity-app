"""
WebSocket handler for real-time agent data streaming.
Connects PWA frontend to Hermes agents via persistent WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import WebSocketException
from jose import jwt, JWTError

from config import settings
from services.agent_context import (
    context_manager,
    AgentContext,
    build_agent_payload,
    build_agent_headers,
    Permission,
)
from services.agent_transformers import AgentTransformers
from services.agent_validation import (
    PulsaOutput,
    DraftOutput,
    RiskScoreOutput,
    SocialOpsOutput,
    AuditOutput,
)

logger = logging.getLogger("websocket-handler")

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """
    Manages WebSocket connections per workspace.
    Routes messages from agents to subscribed clients.
    """

    def __init__(self):
        # workspace_id -> {user_id -> [websockets]}
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        self.connection_lock = asyncio.Lock()

    async def connect(
        self, websocket: WebSocket, workspace_id: str, user_id: str
    ) -> None:
        """Register a new WebSocket connection."""
        await websocket.accept()

        async with self.connection_lock:
            if workspace_id not in self.active_connections:
                self.active_connections[workspace_id] = {}
            if user_id not in self.active_connections[workspace_id]:
                self.active_connections[workspace_id][user_id] = set()

            self.active_connections[workspace_id][user_id].add(websocket)

        logger.info(
            f"✅ WebSocket connected: workspace={workspace_id}, user={user_id}"
        )

    async def disconnect(
        self, websocket: WebSocket, workspace_id: str, user_id: str
    ) -> None:
        """Unregister a WebSocket connection."""
        async with self.connection_lock:
            if (
                workspace_id in self.active_connections
                and user_id in self.active_connections[workspace_id]
            ):
                self.active_connections[workspace_id][user_id].discard(websocket)

                # Cleanup empty structures
                if not self.active_connections[workspace_id][user_id]:
                    del self.active_connections[workspace_id][user_id]
                if not self.active_connections[workspace_id]:
                    del self.active_connections[workspace_id]

        logger.info(
            f"❌ WebSocket disconnected: workspace={workspace_id}, user={user_id}"
        )

    async def broadcast(
        self, workspace_id: str, message: dict, exclude_user: Optional[str] = None
    ) -> None:
        """
        Broadcast message to all connected clients in a workspace.
        Used when agents emit output that affects multiple users.
        """
        if workspace_id not in self.active_connections:
            return

        disconnected = []
        for user_id, websockets in self.active_connections[workspace_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            for websocket in list(websockets):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    disconnected.append((workspace_id, user_id, websocket))

        # Cleanup disconnected sockets
        for ws_id, user_id, ws in disconnected:
            await self.disconnect(ws, ws_id, user_id)

    async def send_personal(
        self, websocket: WebSocket, message: dict
    ) -> None:
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Personal send error: {e}")


# Global connection manager
manager = ConnectionManager()


def verify_ws_token(token: str) -> dict:
    """
    Verify JWT token from WebSocket connection.
    Returns decoded payload with user_id, workspace_id, email.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.error(f"Invalid WebSocket token: {e}")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    """
    WebSocket endpoint: /api/v1/ws?token={JWT}

    Protocol:
    1. Client connects with JWT token
    2. Server validates token, extracts user_id and workspace_id
    3. Client sends: {"type": "subscribe", "agent": "pulso"}
    4. Server streams: {"type": "agent_output", "agent": "pulso", "data": {...}}

    Fallback: If WebSocket drops, client uses HTTP polling endpoint.
    """

    # Auth: verify JWT
    try:
        payload = verify_ws_token(token)
        user_id = payload.get("sub")
        workspace_id = payload.get("workspace_id")
        user_email = payload.get("email")
        permissions = payload.get("permissions") or None

        if not user_id or not workspace_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except WebSocketException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Resolve JWT string identities to canonical governance UUIDs (design D7).
    # On success the context — and therefore access control, audit logging, and the
    # RADAR/AUDIT tenant params — all use the real usuarios.id / tenants.id. On
    # failure we keep the raw values so the per-invoke chokepoint fail-closes with a
    # clear reason instead of crashing the socket.
    try:
        from core.identity_resolver import identity_resolver

        resolved = identity_resolver.resolve(user_id, user_email, workspace_id)
        if resolved.user_uuid:
            user_id = resolved.user_uuid
        if resolved.tenant_uuid:
            workspace_id = resolved.tenant_uuid
        if not resolved.is_complete:
            logger.warning(
                "Identity not fully resolved: sub=%s email=%s workspace=%s "
                "(user_uuid=%s tenant_uuid=%s) — invocations will fail-closed",
                payload.get("sub"),
                user_email,
                payload.get("workspace_id"),
                resolved.user_uuid,
                resolved.tenant_uuid,
            )
    except Exception as exc:  # never break the socket on a resolution error
        logger.error(f"Identity resolution error: {exc}")

    # Create agent context for this session
    agent_context = context_manager.create_context(
        user_id=user_id,
        workspace_id=workspace_id,
        user_email=user_email,
        permissions=permissions,
    )

    # Connect
    await manager.connect(websocket, workspace_id, user_id)
    agent_subscriptions: Set[str] = set()
    heartbeat_task = None
    agent_listeners: Dict[str, asyncio.Task] = {}

    try:
        # Heartbeat: send ping every 30s to keep connection alive
        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        # Listen for client messages
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "subscribe":
                agent = data.get("agent")
                if agent not in agent_subscriptions:
                    agent_subscriptions.add(agent)
                    logger.info(
                        f"📡 Subscribe: workspace={workspace_id}, agent={agent}"
                    )

                    # Start agent listener
                    listener_task = asyncio.create_task(
                        agent_output_listener(
                            agent=agent,
                            context=agent_context,
                            websocket=websocket,
                            manager=manager,
                        )
                    )
                    agent_listeners[agent] = listener_task

            elif msg_type == "unsubscribe":
                agent = data.get("agent")
                if agent in agent_subscriptions:
                    agent_subscriptions.discard(agent)
                    if agent in agent_listeners:
                        agent_listeners[agent].cancel()
                        del agent_listeners[agent]
                    logger.info(
                        f"🔇 Unsubscribe: workspace={workspace_id}, agent={agent}"
                    )

            elif msg_type == "agent_invoke":
                # Synchronous agent invocation from client
                agent = data.get("agent")
                params = data.get("params", {})

                # Check permissions
                if not agent_context.can_invoke_agent(agent):
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "agent_error",
                            "agent": agent,
                            "error": f"Permission denied: cannot invoke {agent}",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    continue

                # Invoke agent with context
                result = await invoke_agent(
                    agent=agent,
                    context=agent_context,
                    params=params,
                )

                await manager.send_personal(
                    websocket,
                    {
                        "type": "agent_output",
                        "agent": agent,
                        "data": result,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup
        await manager.disconnect(websocket, workspace_id, user_id)

        # Invalidate context on disconnect
        context_manager.invalidate_context(workspace_id, user_id)

        if heartbeat_task:
            heartbeat_task.cancel()

        for task in agent_listeners.values():
            task.cancel()

        logger.info(f"WebSocket cleanup: workspace={workspace_id}, user={user_id}")


async def agent_output_listener(
    agent: str,
    context: AgentContext,
    websocket: WebSocket,
    manager: ConnectionManager,
) -> None:
    """Stream agent output via WebSocket.

    Governed by tenant membership verification and audit logging
    (change agent-operations-multitenant-security, Slice 4.4).
    """
    import asyncio
    import time
    from typing import Optional
    from core.agent_access_control import agent_access_control
    from services.agent_cost_tracker import AgentCostTracker
    from services.agent_operations_logger import agent_operations_logger

    # ===== GOVERNANCE LAYER (Slice 4.4) =====
    # Step 1: Tenant membership verification (same gate as invoke_agent)
    access_decision = agent_access_control.check_access(
        context.user_id, context.tenant_id, agent
    )
    if not access_decision.allowed:
        logger.warning(
            f"Stream access denied: user={context.user_id} agent={agent} tenant={context.tenant_id} reason={access_decision.reason}"
        )
        # Log the blocked attempt (async, best-effort, no await).
        asyncio.create_task(
            agent_operations_logger.record(
                tenant_id=context.tenant_id,
                agent_name=agent,
                user_id=context.user_id,
                operation_type="stream",
                status="blocked",
                duration_ms=0,
                cost=0,
                input_data={},
                error_message=access_decision.reason,
            )
        )
        return

    # Step 2: Start timing the stream operation
    start_time = time.perf_counter()
    operation_result = None
    operation_error: Optional[str] = None
    line_count = 0

    AGENT_STREAMS = {
        "pulso": "/api/v1/agents/pulso-diario/stream",
        "centinela": "/api/v1/centinela/stream",
        "radar": "/api/v1/agents/radar-predictivo/stream",
        "taty": "/api/v1/agents/taty/stream",
        "social-ops": "/api/v1/agents/social-ops/stream",
        "audit": "/api/v1/agents/auditoria-sombra/stream",
        "approval": "/api/v1/approval-queue/stream",
        "maestro": "/api/v1/hermes/swarm/stream",
    }

    stream_endpoint = AGENT_STREAMS.get(agent)
    if not stream_endpoint:
        logger.warning(f"No stream endpoint for {agent}")
        operation_error = "no_stream_endpoint"
        operation_result = {"status": "failed"}
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "GET",
                f"http://localhost:8000{stream_endpoint}",
                headers=build_agent_headers(context),
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    line_count += 1
                    try:
                        data = json.loads(line)
                        await manager.send_personal(
                            websocket,
                            {
                                "type": "agent_output",
                                "agent": agent,
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )
                    except json.JSONDecodeError:
                        logger.debug(f"Non-JSON line from {agent}: {line}")

        operation_result = {"status": "success", "line_count": line_count}

    except asyncio.CancelledError:
        logger.info(f"Agent listener cancelled: {agent}")
        operation_error = "cancelled"
        operation_result = {"status": "failed", "line_count": line_count}
    except Exception as e:
        logger.error(f"Stream error ({agent}): {e}")
        operation_error = str(e)
        operation_result = {"status": "failed", "line_count": line_count}

    finally:
        # ===== AUDIT LOGGING (Slice 4.4, best-effort) =====
        if operation_result is not None:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            operation_status = operation_result.get("status")

            # Determine cost (same logic as invoke_agent).
            cost_tracker = AgentCostTracker()
            final_cost = cost_tracker.resolve_cost_for_status(
                agent, "stream", status=operation_status
            )

            # Log operation asynchronously (best-effort; never blocks WebSocket).
            asyncio.create_task(
                agent_operations_logger.record(
                    tenant_id=context.tenant_id,
                    agent_name=agent,
                    user_id=context.user_id,
                    operation_type="stream",
                    status=operation_status,
                    duration_ms=elapsed_ms,
                    cost=final_cost,
                    input_data={},
                    output_data={"line_count": line_count},
                    error_message=operation_error,
                )
            )


async def invoke_agent(agent: str, context: AgentContext, params: dict) -> dict:
    """Invoke real Hermes agent endpoint with data transformation.

    Governed by tenant membership verification, cost tracking, and audit logging
    (change agent-operations-multitenant-security, Slice 4).
    """
    import asyncio
    import time
    from typing import Optional
    from core.agent_access_control import agent_access_control
    from services.agent_cost_tracker import AgentCostTracker
    from services.agent_operations_logger import agent_operations_logger

    AGENT_ENDPOINTS = {
        "pulso": "/api/v1/agents/pulso-diario/summary",
        "centinela": "/api/v1/centinela/generate-draft",
        "radar": "/api/v1/agents/radar-predictivo/risk-score",
        "taty": "/api/v1/agents/taty/invoke",
        "social-ops": "/api/v1/agents/social-ops/status",
        "audit": "/api/v1/agents/auditoria-sombra/report",
        "approval": "/api/v1/approval-queue/enqueue",
        "maestro": "/api/v1/hermes/swarm/invoke",
    }

    endpoint = AGENT_ENDPOINTS.get(agent)
    if not endpoint:
        return {"status": "error", "message": f"Unknown agent: {agent}"}

    logger.info(
        f"Invoking agent: {agent}, workspace={context.workspace_id}, user={context.user_id}"
    )

    # ===== GOVERNANCE LAYER (Slice 4) =====
    # Step 1: Tenant membership verification
    access_decision = agent_access_control.check_access(
        context.user_id, context.tenant_id, agent
    )
    if not access_decision.allowed:
        logger.warning(
            f"Access denied: user={context.user_id} agent={agent} tenant={context.tenant_id} reason={access_decision.reason}"
        )
        # Log the blocked attempt (async, best-effort, no await).
        asyncio.create_task(
            agent_operations_logger.record(
                tenant_id=context.tenant_id,
                agent_name=agent,
                user_id=context.user_id,
                operation_type="invoke",
                status="blocked",
                duration_ms=0,
                cost=0,
                input_data={"params": params},
                error_message=access_decision.reason,
            )
        )
        return {
            "status": "error",
            "message": f"Access denied: {access_decision.reason}",
        }

    # Step 2: Start timing the operation
    start_time = time.perf_counter()
    operation_result = None
    operation_error: Optional[str] = None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = build_agent_headers(context)
            payload = build_agent_payload(context, params)

            # Add required parameters per agent
            if agent == "radar":
                # RADAR expects tenant_id as query param
                response = await client.post(
                    f"http://localhost:8000{endpoint}",
                    params={"tenant_id": context.workspace_id},
                    json=payload,
                    headers=headers,
                )
            elif agent == "audit":
                # AUDIT expects tenant_id and date_start in body
                audit_payload = {
                    **payload,
                    "tenant_id": context.workspace_id,
                    "date_start": params.get("date_start", "2026-01-01"),
                }
                response = await client.post(
                    f"http://localhost:8000{endpoint}",
                    json=audit_payload,
                    headers=headers,
                )
            elif agent == "approval":
                # APPROVAL expects draft_id and draft_type in body
                approval_payload = {
                    **payload,
                    "draft_id": params.get("draft_id", ""),
                    "draft_type": params.get("draft_type", "pending"),
                }
                response = await client.post(
                    f"http://localhost:8000{endpoint}",
                    json=approval_payload,
                    headers=headers,
                )
            else:
                response = await client.post(
                    f"http://localhost:8000{endpoint}",
                    json=payload,
                    headers=headers,
                )

            if response.status_code >= 400:
                logger.error(
                    f"Agent error ({agent}): {response.status_code} {response.text}"
                )
                operation_error = response.text
                operation_result = {
                    "status": "error",
                    "code": response.status_code,
                    "message": response.text,
                }
                return operation_result

            raw_data = response.json()

            # Apply transformations and validate based on agent type
            try:
                if agent == "pulso":
                    data = AgentTransformers.transform_pulso(raw_data)
                    validated = PulsaOutput(**data)
                    data = validated.model_dump()
                elif agent == "centinela":
                    data = AgentTransformers.transform_centinela(raw_data)
                elif agent == "radar":
                    data = AgentTransformers.transform_radar(raw_data)
                    validated = RiskScoreOutput(**data)
                    data = validated.model_dump()
                elif agent == "social-ops":
                    data = AgentTransformers.transform_social_ops(raw_data)
                    validated = SocialOpsOutput(**data)
                    data = validated.model_dump()
                elif agent == "audit":
                    data = AgentTransformers.transform_audit(raw_data)
                    validated = AuditOutput(**data)
                    data = validated.model_dump()
                else:
                    # No transformation for taty, approval, maestro
                    data = raw_data
            except ValueError as e:
                logger.error(f"Data validation failed ({agent}): {e}")
                operation_error = str(e)
                operation_result = {
                    "status": "error",
                    "message": f"Invalid agent response format: {str(e)}",
                }
                return operation_result

            # Compute cost and accumulate to session (Slice 4: cost tracking).
            cost_tracker = AgentCostTracker()
            cost = cost_tracker.resolve_cost_for_status(agent, "invoke", status="success")
            if not hasattr(context, "_session_cost"):
                context._session_cost = 0
            context._session_cost += float(cost)

            operation_result = {
                "status": "success",
                "agent": agent,
                "data": data,
                "cost": float(cost),
                "session_cost": context._session_cost,
            }
            return operation_result

    except Exception as e:
        logger.error(f"Agent invocation failed ({agent}): {e}")
        operation_error = str(e)
        operation_result = {"status": "error", "message": str(e)}
        return operation_result

    finally:
        # ===== AUDIT LOGGING (Slice 4, best-effort) =====
        # Calculate duration and log the operation (async, non-blocking).
        if operation_result is not None:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            # Map the client-facing result status to the agent_operations taxonomy
            # (success | failed | blocked). invoke_agent returns "error" to the
            # client on failure, but the audit table CHECK only accepts "failed";
            # logging "error" silently violates the constraint and writes no row.
            raw_status = operation_result.get("status")
            operation_status = "success" if raw_status == "success" else "failed"

            # Determine cost: if blocked or errored, zero; else use cost tracker.
            cost_tracker = AgentCostTracker()
            final_cost = cost_tracker.resolve_cost_for_status(
                agent, "invoke", status=operation_status
            )

            # Log operation asynchronously (best-effort; never blocks the response).
            asyncio.create_task(
                agent_operations_logger.record(
                    tenant_id=context.tenant_id,
                    agent_name=agent,
                    user_id=context.user_id,
                    operation_type="invoke",
                    status=operation_status,
                    duration_ms=elapsed_ms,
                    cost=final_cost,
                    input_data={"params": params},
                    output_data=(
                        operation_result.get("data") if operation_status == "success" else None
                    ),
                    error_message=operation_error,
                )
            )
