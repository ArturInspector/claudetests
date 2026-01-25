from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_returns_summary(client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await client.post(
        "/api/v1/sessions",
        json={"topic": "Databases", "level": None},
        headers=auth_headers,
    )
    session_id = create_res.json()["id"]

    res = await client.post(f"/api/v1/analyze/{session_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["summary"].startswith("fake-response")


@pytest.mark.asyncio
async def test_analyze_not_found(client: AsyncClient, auth_headers: dict[str, str]):
    res = await client.post("/api/v1/analyze/9999", headers=auth_headers)
    assert res.status_code == 404

