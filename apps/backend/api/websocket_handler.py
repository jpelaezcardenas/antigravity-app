"""
WebSocket handler for real-time agent data streaming.
Connects PWA frontend to Hermes agents via persistent WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import WebSocketException
import jwt

from config import settings

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
    except jwt.InvalidTokenError as e:
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

        if not user_id or not workspace_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except WebSocketException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

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
                            workspace_id=workspace_id,
                            user_id=user_id,
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

                # Invoke agent with context
                result = await invoke_agent(
                    agent=agent,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    user_email=user_email,
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

        if heartbeat_task:
            heartbeat_task.cancel()

        for task in agent_listeners.values():
            task.cancel()

        logger.info(f"WebSocket cleanup: workspace={workspace_id}, user={user_id}")


async def agent_output_listener(
    agent: str,
    workspace_id: str,
    user_id: str,
    websocket: WebSocket,
    manager: ConnectionManager,
) -> None:
    """
    Listen for agent output and stream to client.
    This is a stub that polls or subscribes to agent output.

    TODO: Replace with actual Hermes integration:
    - Subscribe to Hermes event stream
    - Filter by workspace_id
    - Stream results via WebSocket
    """
    try:
        # Placeholder: in production, subscribe to Hermes agent output
        # For now, we just keep the listener alive
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Agent listener error ({agent}): {e}")


async def invoke_agent(
    agent: str,
    workspace_id: str,
    user_id: str,
    user_email: str,
    params: dict,
) -> dict:
    """
    Invoke a Hermes agent with context.

    This function:
    1. Builds agent context (workspace, user, permissions)
    2. Calls Hermes via HTTP (or direct integration)
    3. Returns result

    TODO: Replace with actual Hermes integration.
    For now, returns stub data.
    """

    agent_context = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "user_email": user_email,
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"🤖 Invoking agent: agent={agent}, workspace={workspace_id}, user={user_id}"
    )

    # TODO: Call actual agent endpoints
    # POST https://antigravity-app-production-175a.up.railway.app/api/v1/agents/{agent}/invoke
    # with context + params

    return {
        "agent": agent,
        "status": "success",
        "context": agent_context,
        "params": params,
        "result": {"placeholder": "Agent output will be populated here"},
    }
