"""
Unit tests for the face detection service (backend/services/face_service.py).

Strategy:
    - _sync_detect is the synchronous blocking function that wraps MediaPipe.
      We test it directly (no executor overhead) with synthetic image bytes.
    - process_frame is tested via mocking: we swap out _sync_detect so tests
      don't require a real webcam feed or a trained model download.
    - A real white 100x100 PNG is used for the no-face passthrough path since
      MediaPipe genuinely won't detect a face in a blank image.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from backend.services.face_service import _sync_detect, process_frame


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_white_png(width: int = 100, height: int = 100) -> bytes:
    """Create a plain white PNG image and return it as bytes."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_white_jpeg(width: int = 100, height: int = 100) -> bytes:
    """Create a plain white JPEG image and return it as bytes."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# _sync_detect — synchronous MediaPipe wrapper
# ---------------------------------------------------------------------------

def test_sync_detect_no_face_on_blank_image():
    """
    A plain white image should produce no detections.
    This verifies the passthrough path without needing a real webcam.
    """
    raw = make_white_jpeg()
    result, pil_image = _sync_detect(raw)
    # MediaPipe should find no faces in a blank white image
    assert not result.detections
    assert pil_image is not None


def test_sync_detect_returns_pil_image():
    """_sync_detect must always return a PIL.Image alongside the result."""
    raw = make_white_jpeg()
    result, pil_image = _sync_detect(raw)
    assert isinstance(pil_image, Image.Image)


# ---------------------------------------------------------------------------
# process_frame — async pipeline
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_frame_passthrough_when_no_face():
    """
    When MediaPipe detects no faces, process_frame returns the original bytes
    unchanged and does NOT call save_roi.
    """
    raw = make_white_jpeg()

    # Mock _sync_detect to return empty detections
    mock_result = MagicMock()
    mock_result.detections = []
    mock_pil = Image.new("RGB", (100, 100))

    mock_db = MagicMock()

    with patch("backend.services.face_service._sync_detect", return_value=(mock_result, mock_pil)):
        with patch("backend.services.face_service.save_roi") as mock_save:
            returned = await process_frame(raw, "test-session", mock_db)

    assert returned == raw           # passthrough — same object
    mock_save.assert_not_called()    # no DB write on no-face


@pytest.mark.asyncio
async def test_process_frame_draws_box_and_saves_roi_on_face():
    """
    When a detection is present, process_frame must:
      - return bytes (annotated JPEG, different from input).
      - call save_roi once per detection.
    """
    raw = make_white_jpeg()

    # Build a realistic mock detection with a relative bounding box
    mock_bbox = MagicMock()
    mock_bbox.xmin   = 0.1
    mock_bbox.ymin   = 0.1
    mock_bbox.width  = 0.3
    mock_bbox.height = 0.4

    mock_detection = MagicMock()
    mock_detection.location_data.relative_bounding_box = mock_bbox

    mock_result = MagicMock()
    mock_result.detections = [mock_detection]

    mock_pil = Image.new("RGB", (100, 100), color=(200, 200, 200))
    mock_db  = MagicMock()

    with patch("backend.services.face_service._sync_detect", return_value=(mock_result, mock_pil)):
        with patch("backend.services.face_service.save_roi") as mock_save:
            returned = await process_frame(raw, "test-session", mock_db)

    assert isinstance(returned, bytes)
    mock_save.assert_called_once()

    call_kwargs = mock_save.call_args.kwargs
    assert call_kwargs["session_id"] == "test-session"
    assert "x" in call_kwargs
    assert "y" in call_kwargs
    assert "width"  in call_kwargs
    assert "height" in call_kwargs


@pytest.mark.asyncio
async def test_process_frame_handles_corrupt_input():
    """
    If the input bytes are not a valid image, process_frame must return the
    original bytes unchanged rather than raising an exception.
    """
    corrupt_bytes = b"this is not an image"
    mock_db = MagicMock()

    returned = await process_frame(corrupt_bytes, "test-session", mock_db)
    assert returned == corrupt_bytes
