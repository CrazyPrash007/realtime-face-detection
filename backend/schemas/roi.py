from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ROIEventSchema(BaseModel):
    """API response schema for a single ROI detection event."""
    id: str
    session_id: str
    timestamp: datetime
    x: int
    y: int
    width: int
    height: int

    model_config = {"from_attributes": True}


class ROIListResponse(BaseModel):
    """Paginated wrapper for ROI event lists."""
    total: int
    limit: int
    offset: int
    items: list[ROIEventSchema]
