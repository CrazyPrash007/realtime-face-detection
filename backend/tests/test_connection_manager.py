"""
Unit tests for ConnectionManager (backend/api/connection_manager.py).

Tests are fully synchronous / in-process — no real WebSocket server is started.
We mock the WebSocket objects to avoid network I/O.

Covers:
    - connect_viewer registers viewer and tracks IP count.
    - disconnect_viewer removes viewer and decrements IP count.
    - Empty session entries are cleaned up after last viewer disconnects.
    - broadcast sends bytes to all viewers in a session.
    - Stale (broken) WebSocket connections are silently pruned during broadcast.
    - IP limit: the (MAX+1)th connection from the same IP is rejected.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocketDisconnect

from backend.api.connection_manager import ConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ws(host: str = "127.0.0.1") -> MagicMock:
    """Return a mock WebSocket with a configurable client IP."""
    ws = MagicMock()
    ws.client = MagicMock()
    ws.client.host = host
    ws.accept = AsyncMock()
    ws.close  = AsyncMock()
    ws.send_bytes = AsyncMock()
    return ws


# ---------------------------------------------------------------------------
# connect_viewer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_connect_viewer_registers_websocket():
    mgr = ConnectionManager()
    ws = make_ws()

    await mgr.connect_viewer("session-1", ws)

    assert ws in mgr.active_connections["session-1"]
    assert mgr.ip_counts["127.0.0.1"] == 1
    ws.accept.assert_called_once()


@pytest.mark.asyncio
async def test_connect_multiple_viewers_same_session():
    mgr = ConnectionManager()
    ws1 = make_ws("1.1.1.1")
    ws2 = make_ws("2.2.2.2")

    await mgr.connect_viewer("session-x", ws1)
    await mgr.connect_viewer("session-x", ws2)

    assert len(mgr.active_connections["session-x"]) == 2


# ---------------------------------------------------------------------------
# disconnect_viewer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_viewer_removes_entry():
    mgr = ConnectionManager()
    ws = make_ws()

    await mgr.connect_viewer("session-1", ws)
    mgr.disconnect_viewer("session-1", ws)

    assert ws not in mgr.active_connections.get("session-1", [])
    assert mgr.ip_counts["127.0.0.1"] == 0


@pytest.mark.asyncio
async def test_disconnect_cleans_up_empty_session():
    """After the last viewer leaves, the session key must be removed."""
    mgr = ConnectionManager()
    ws = make_ws()

    await mgr.connect_viewer("session-cleanup", ws)
    mgr.disconnect_viewer("session-cleanup", ws)

    assert "session-cleanup" not in mgr.active_connections


@pytest.mark.asyncio
async def test_disconnect_nonexistent_viewer_is_safe():
    """Disconnecting a WS that was never registered must not raise."""
    mgr = ConnectionManager()
    ws = make_ws()
    mgr.disconnect_viewer("nonexistent", ws)  # should not raise


# ---------------------------------------------------------------------------
# broadcast
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_broadcast_sends_to_all_viewers():
    mgr = ConnectionManager()
    ws1 = make_ws("10.0.0.1")
    ws2 = make_ws("10.0.0.2")

    await mgr.connect_viewer("session-b", ws1)
    await mgr.connect_viewer("session-b", ws2)

    payload = b"frame_data"
    await mgr.broadcast("session-b", payload)

    ws1.send_bytes.assert_called_once_with(payload)
    ws2.send_bytes.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_broadcast_prunes_broken_connections():
    """A viewer whose send_bytes raises must be silently removed."""
    mgr = ConnectionManager()
    good_ws  = make_ws("10.0.0.1")
    broken_ws = make_ws("10.0.0.2")
    broken_ws.send_bytes = AsyncMock(side_effect=Exception("connection lost"))

    await mgr.connect_viewer("session-prune", good_ws)
    await mgr.connect_viewer("session-prune", broken_ws)

    await mgr.broadcast("session-prune", b"data")

    good_ws.send_bytes.assert_called_once()
    assert broken_ws not in mgr.active_connections.get("session-prune", [])


@pytest.mark.asyncio
async def test_broadcast_unknown_session_is_safe():
    """Broadcasting to a session with no viewers must not raise."""
    mgr = ConnectionManager()
    await mgr.broadcast("no-such-session", b"data")  # should not raise


# ---------------------------------------------------------------------------
# IP rate limiting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ip_limit_enforced(monkeypatch):
    """The (MAX+1)th connection from the same IP must be closed and raise."""
    from backend.core import config as cfg

    mgr = ConnectionManager()
    max_conn = 3
    monkeypatch.setattr(cfg.settings, "MAX_WS_CONNECTIONS", max_conn)

    # Fill up to the limit — all should succeed
    for i in range(max_conn):
        ws = make_ws("9.9.9.9")
        await mgr.connect_viewer(f"session-{i}", ws)

    # One more from the same IP must be rejected
    extra_ws = make_ws("9.9.9.9")
    with pytest.raises(WebSocketDisconnect):
        await mgr.connect_viewer("session-extra", extra_ws)

    extra_ws.close.assert_called_once_with(code=1008)
