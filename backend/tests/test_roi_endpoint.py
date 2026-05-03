"""
Tests for GET /api/v1/roi

Covers:
    - Happy path returns 200 with expected schema fields.
    - limit=0  → 422 (below minimum of 1).
    - limit=501 → 422 (above maximum of 500).
    - limit=500 → 200 (boundary accepted).
    - offset=0  → 200 (zero is valid).
    - session_id filter is passed through without error.
"""

import pytest


@pytest.mark.asyncio
async def test_roi_returns_200_with_schema(client):
    """Basic happy-path: endpoint exists and returns the expected response shape."""
    response = await client.get("/api/v1/roi")
    assert response.status_code == 200

    data = response.json()
    assert "items"  in data
    assert "total"  in data
    assert "limit"  in data
    assert "offset" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_roi_default_pagination(client):
    """Default limit and offset are reflected in the response."""
    response = await client.get("/api/v1/roi")
    data = response.json()
    assert data["limit"]  == 50
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_roi_limit_too_low_returns_422(client):
    """limit=0 is below the ge=1 bound and must be rejected."""
    response = await client.get("/api/v1/roi?limit=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_roi_limit_too_high_returns_422(client):
    """limit=501 exceeds le=500 and must be rejected."""
    response = await client.get("/api/v1/roi?limit=501")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_roi_limit_boundary_accepted(client):
    """limit=500 is the maximum allowed value and must return 200."""
    response = await client.get("/api/v1/roi?limit=500")
    assert response.status_code == 200
    assert response.json()["limit"] == 500


@pytest.mark.asyncio
async def test_roi_negative_offset_returns_422(client):
    """Negative offset violates ge=0 and must be rejected."""
    response = await client.get("/api/v1/roi?offset=-1")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_roi_session_id_filter(client):
    """Passing session_id returns 200 (even if no matching records exist)."""
    response = await client.get("/api/v1/roi?session_id=test-session-abc")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Liveness probe must return 200 and status=ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
