import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


class ROIEvent(Base):
    """
    Stores one bounding-box detection per processed video frame.

    Columns:
        id         – UUID primary key.
        session_id – Groups events belonging to a single streaming session.
                     Indexed to allow efficient per-session REST queries.
        timestamp  – UTC wall-clock time of detection (indexed for time-range queries).
        x, y       – Top-left corner of the bounding box in pixels.
        width      – Width of the bounding box in pixels.
        height     – Height of the bounding box in pixels.
    """
    __tablename__ = "roi_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    # Composite index for the most common REST query: filter by session, ordered by time
    __table_args__ = (
        Index("ix_roi_session_time", "session_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<ROIEvent id={self.id!r} session={self.session_id!r} "
            f"ts={self.timestamp.isoformat()} box=({self.x},{self.y},{self.width},{self.height})>"
        )
