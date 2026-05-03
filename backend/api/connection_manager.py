"""
ConnectionManager — manages WebSocket viewer sessions and per-IP rate limiting.

Design decisions:
- Backend owns session_id creation; viewers connect by referencing an existing id.
- ip_counts prevents a single client from exhausting server file descriptors.
- All mutations are single-threaded (asyncio event loop), so no locks are needed.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect
from backend.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Tracks active viewer WebSocket connections grouped by session_id.

    Attributes:
        active_connections: session_id → list of viewer WebSockets.
        ip_counts:          client IP → number of active connections from that IP.
    """

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.ip_counts: Dict[str, int] = defaultdict(int)

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect_viewer(self, session_id: str, websocket: WebSocket) -> None:
        """
        Accept and register a viewer WebSocket for the given session.

        Raises:
            WebSocketDisconnect: if the originating IP already has
                MAX_WS_CONNECTIONS active connections.
        """
        client_ip = self._get_ip(websocket)

        if self.ip_counts[client_ip] >= settings.MAX_WS_CONNECTIONS:
            logger.warning(
                "IP %s exceeded connection limit (%d), rejecting viewer for session %s",
                client_ip,
                settings.MAX_WS_CONNECTIONS,
                session_id,
            )
            await websocket.close(code=1008)  # 1008 = Policy Violation
            raise WebSocketDisconnect(code=1008)

        await websocket.accept()
        self.active_connections[session_id].append(websocket)
        self.ip_counts[client_ip] += 1

        logger.info(
            "Viewer connected — session=%s ip=%s total_viewers=%d",
            session_id,
            client_ip,
            len(self.active_connections[session_id]),
        )

    def disconnect_viewer(self, session_id: str, websocket: WebSocket) -> None:
        """Remove a viewer WebSocket and decrement the IP counter."""
        connections = self.active_connections.get(session_id, [])
        if websocket in connections:
            connections.remove(websocket)

        client_ip = self._get_ip(websocket)
        if self.ip_counts[client_ip] > 0:
            self.ip_counts[client_ip] -= 1

        # clean up empty session entries
        if not connections:
            self.active_connections.pop(session_id, None)

        logger.info(
            "Viewer disconnected — session=%s ip=%s remaining_viewers=%d",
            session_id,
            client_ip,
            len(connections),
        )

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(self, session_id: str, data: bytes) -> None:
        """
        Send processed frame bytes to all viewers subscribed to session_id.

        Stale connections are silently removed.
        """
        viewers = list(self.active_connections.get(session_id, []))
        dead: List[WebSocket] = []

        for ws in viewers:
            try:
                await ws.send_bytes(data)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect_viewer(session_id, ws)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_ip(websocket: WebSocket) -> str:
        """Extract the client IP, falling back to 'unknown'."""
        if websocket.client:
            return websocket.client.host
        return "unknown"


# Singleton — shared across the entire application lifetime.
manager = ConnectionManager()
