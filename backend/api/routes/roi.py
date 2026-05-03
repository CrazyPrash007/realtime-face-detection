"""
REST endpoint for querying stored ROI detection events.

GET /api/v1/roi
    Query params:
        session_id  – (optional) filter to a specific streaming session.
        limit       – number of records to return; 1–500, default 50.
        offset      – pagination offset; default 0.

    Returns ROIListResponse (total count + paginated items).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.schemas.roi import ROIListResponse, ROIEventSchema
from backend.services.roi_service import fetch_roi, count_roi

router = APIRouter(prefix="/api/v1", tags=["roi"])


@router.get(
    "/roi",
    response_model=ROIListResponse,
    summary="List ROI detection events",
    description=(
        "Returns a paginated list of bounding-box detection events. "
        "Optionally filter by session_id. Ordered newest-first."
    ),
)
async def list_roi(
    session_id: Optional[str] = Query(
        default=None,
        description="Filter events to a single streaming session.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of records to return (1–500).",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip for pagination.",
    ),
    db: AsyncSession = Depends(get_db),
) -> ROIListResponse:
    items = await fetch_roi(db, session_id=session_id, limit=limit, offset=offset)
    total = await count_roi(db, session_id=session_id)

    return ROIListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ROIEventSchema.model_validate(item) for item in items],
    )
