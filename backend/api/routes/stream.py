"""
WebSocket streaming endpoints.

Protocol:
    /stream/upload  — Uploader (frontend webcam)
        1. Client connects (no session_id needed).
        2. Server accepts and immediately sends {"session_id": "<uuid>"}.
        3. Client sends raw JPEG bytes for each frame.
        4. Server runs face detection and broadcasts processed frame to viewers.

    /stream/view?session_id=<uuid>  — Viewer (display panel)
        1. Client connects with an existing session_id (obtained from the upload socket).
        2. Server registers as a viewer and forwards processed frames as binary messages.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.api.connection_manager import manager
from backend.core.config import settings
from backend.db.database import get_db
from backend.services.face_service import process_frame

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


@router.websocket("/stream/upload")
async def upload_stream(websocket: WebSocket) -> None:
    """
    Uploader endpoint.

    The backend generates the session_id to prevent clients from hijacking
    each other's streams. The generated id is sent back as the very first
    message so the frontend can share it with the viewer panel.
    """
    await websocket.accept()

    # Audit fix #1: backend owns session_id creation.
    session_id = str(uuid.uuid4())
    await websocket.send_json({"session_id": session_id})
    logger.info("Upload session started: %s", session_id)

    try:
        async for db in get_db():
            while True:
                try:
                    raw_bytes: bytes = await websocket.receive_bytes()
                except WebSocketDisconnect:
                    logger.info("Uploader disconnected: %s", session_id)
                    return

                # Audit fix — enforce frame size cap against DoS.
                if len(raw_bytes) > settings.MAX_FRAME_BYTES:
                    logger.warning(
                        "Frame too large (%d bytes) from session %s, skipping.",
                        len(raw_bytes),
                        session_id,
                    )
                    continue

                processed: bytes = await process_frame(raw_bytes, session_id, db)
                await manager.broadcast(session_id, processed)

    except WebSocketDisconnect:
        logger.info("Upload session ended: %s", session_id)
    except Exception as exc:
        logger.exception("Unexpected error in upload session %s: %s", session_id, exc)
        await websocket.close(code=1011)


@router.websocket("/stream/view")
async def view_stream(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID received from the upload socket"),
) -> None:
    """
    Viewer endpoint.

    Clients must supply the session_id obtained from the uploader's first
    message. Processed frames are forwarded as binary WebSocket messages.
    """
    try:
        await manager.connect_viewer(session_id, websocket)
    except WebSocketDisconnect:
        return  # IP limit exceeded; socket already closed by manager

    try:
        # Keep the connection alive; the manager pushes frames via broadcast().
        while True:
            # receive_text() blocks until the client sends a ping or disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Viewer disconnected from session: %s", session_id)
    finally:
        manager.disconnect_viewer(session_id, websocket)
