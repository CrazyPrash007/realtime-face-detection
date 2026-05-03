"""
Face detection service using MediaPipe and Pillow.

Key design decisions:
    - MediaPipe's .process() is a blocking CPU operation. Running it directly
      inside an async handler would freeze every other WebSocket connection for
      the duration of the call. Fix #2 from the audit: we offload it to a
      thread-pool executor so the event loop stays responsive.

    - No OpenCV. Frame decoding uses PIL.Image; bounding-box drawing uses
      PIL.ImageDraw. The processed frame is re-encoded as JPEG.

    - No-face passthrough: if MediaPipe finds no detections the original bytes
      are returned unchanged and no database write is performed, avoiding
      unnecessary I/O.

    - The MediaPipe FaceDetection model is constructed once at module load and
      reused across all calls (thread-safe for read-only inference).
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Optional

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.services.roi_service import save_roi

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level MediaPipe detector (created once, reused across threads)
# ---------------------------------------------------------------------------
_mp_face = mp.solutions.face_detection
_detector = _mp_face.FaceDetection(
    model_selection=0,       # 0 = short-range model (≤ 2 m); best for webcam
    min_detection_confidence=settings.MEDIAPIPE_CONFIDENCE,
)

# Bounding-box style constants
_BOX_COLOR = (0, 230, 118)   # vivid green
_BOX_WIDTH = 3               # pixels


# ---------------------------------------------------------------------------
# Synchronous detection (runs inside executor thread)
# ---------------------------------------------------------------------------

def _sync_detect(raw_bytes: bytes):
    """
    Decode JPEG bytes, run MediaPipe face detection, return the result object.

    This function is intentionally synchronous so it can be safely offloaded
    to a thread-pool executor.
    """
    image: Image.Image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    rgb_array = np.array(image)
    return _detector.process(rgb_array), image


def _draw_boxes(
    image: Image.Image,
    detections,
) -> tuple[Image.Image, list[dict]]:
    """
    Draw bounding boxes on the image using PIL.ImageDraw.

    Returns the annotated image and a list of box dicts
    (keys: x, y, width, height — absolute pixel values).
    """
    draw = ImageDraw.Draw(image)
    img_w, img_h = image.size
    boxes: list[dict] = []

    for detection in detections:
        bbox = detection.location_data.relative_bounding_box

        # Convert relative → absolute pixel coords
        x = int(bbox.xmin * img_w)
        y = int(bbox.ymin * img_h)
        w = int(bbox.width * img_w)
        h = int(bbox.height * img_h)

        # Clamp to image boundaries
        x = max(0, x)
        y = max(0, y)
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        draw.rectangle(
            [x, y, x + w, y + h],
            outline=_BOX_COLOR,
            width=_BOX_WIDTH,
        )
        boxes.append({"x": x, "y": y, "width": w, "height": h})

    return image, boxes


def _encode_jpeg(image: Image.Image, quality: int = 85) -> bytes:
    """Re-encode a PIL Image to JPEG bytes."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def process_frame(
    raw_bytes: bytes,
    session_id: str,
    db: AsyncSession,
) -> bytes:
    """
    Detect faces in a JPEG frame and return the annotated frame bytes.

    Flow:
        1. Offload blocking MediaPipe call to thread executor (audit fix #2).
        2. If no faces detected → return original bytes unchanged (passthrough).
        3. If faces detected → draw bounding boxes with PIL, persist each ROI
           to the database asynchronously, return annotated JPEG bytes.

    Args:
        raw_bytes:  Raw JPEG frame from the WebSocket uploader.
        session_id: Session identifier used to group DB records.
        db:         Async SQLAlchemy session (injected by FastAPI dependency).

    Returns:
        JPEG bytes — either annotated (face found) or original (no face).
    """
    loop = asyncio.get_event_loop()

    try:
        # Audit fix #2: run CPU-bound MediaPipe in executor
        results, pil_image = await loop.run_in_executor(
            None, _sync_detect, raw_bytes
        )
    except Exception as exc:
        logger.warning("Frame decode/detect failed: %s — passing through.", exc)
        return raw_bytes

    if not results.detections:
        # No face → passthrough, no DB write
        return raw_bytes

    # Draw boxes and collect absolute pixel coordinates
    annotated, boxes = _draw_boxes(pil_image, results.detections)

    # Persist each detection asynchronously (non-blocking)
    for box in boxes:
        try:
            await save_roi(
                db,
                session_id=session_id,
                x=box["x"],
                y=box["y"],
                width=box["width"],
                height=box["height"],
            )
        except Exception as exc:
            logger.error("Failed to save ROI for session %s: %s", session_id, exc)

    return _encode_jpeg(annotated)
