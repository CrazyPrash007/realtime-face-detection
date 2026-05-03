"""
FastAPI application entry point.

Startup sequence (lifespan):
    1. Create all database tables if they don't exist (idempotent).

Security:
    - CORS origins are loaded from .env via pydantic_settings.
    - No wildcard origins are permitted.

Endpoints registered:
    /api/v1/roi    – REST (see api/routes/roi.py)
    /stream/upload – WebSocket uploader (see api/routes/stream.py)
    /stream/view   – WebSocket viewer  (see api/routes/stream.py)
    /health        – Liveness probe for Docker healthcheck
    /docs          – Auto-generated OpenAPI UI (FastAPI default)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.db.init_db import create_tables
from backend.api.routes.roi import router as roi_router
from backend.api.routes.stream import router as stream_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before yielding to the request handler."""
    logger.info("Starting up — creating database tables…")
    await create_tables()
    logger.info("Database tables ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Real-Time Face Detection API",
    description=(
        "Accepts webcam frames over WebSocket, detects faces with MediaPipe + Pillow, "
        "stores bounding-box (ROI) data in PostgreSQL, and streams the processed feed "
        "to viewer clients."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — Audit fix #1 / Phase 6: never use wildcard origins
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(roi_router)
app.include_router(stream_router)


# ---------------------------------------------------------------------------
# Health check — Audit fix #7: required for Docker healthcheck
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"], summary="Liveness probe")
async def health() -> dict:
    """Returns 200 OK when the service is running."""
    return {"status": "ok"}
