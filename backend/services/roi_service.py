from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import ROIEvent


async def save_roi(
    db: AsyncSession,
    *,
    session_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> ROIEvent:
    """Persist a single ROI detection to the database."""
    event = ROIEvent(
        session_id=session_id,
        x=x,
        y=y,
        width=width,
        height=height,
    )
    db.add(event)
    await db.flush()   # assign id without closing the session
    return event


async def fetch_roi(
    db: AsyncSession,
    *,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ROIEvent]:
    """
    Retrieve ROI events, optionally filtered by session_id.
    Results are ordered by timestamp descending (newest first).
    """
    stmt = select(ROIEvent).order_by(ROIEvent.timestamp.desc())

    if session_id:
        stmt = stmt.where(ROIEvent.session_id == session_id)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())
