from __future__ import annotations

import pytest
from httpx import AsyncClient

from .fakes import FakeRAG


@pytest.mark.asyncio
async def test_session_crud_and_answer_flow(
    client: AsyncClient, auth_headers: dict[str, str], fake_rag: FakeRAG
):
    # create
    create_res = await client.post(
        "/api/v1/sessions",
        json={"topic": "CAP theorem", "level": "beginner"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # list
    list_res = await client.get("/api/v1/sessions", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()[0]["id"] == session_id

    # detail empty iterations
    detail_res = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["iterations"] == []

    # answer
    answer_res = await client.post(
        f"/api/v1/sessions/{session_id}/answer",
        json={"question": "What is CAP?", "answer": "Consistency Availability Partition"},
        headers=auth_headers,
    )
    assert answer_res.status_code == 200
    answer_data = answer_res.json()
    assert answer_data["iteration"]["feedback"].startswith("fake-response")
    assert answer_data["similar_context"] == fake_rag.similar
    assert fake_rag.indexed and fake_rag.indexed[0]["session_id"] == session_id

    # delete
    del_res = await client.delete(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert del_res.status_code == 204
    assert fake_rag.deleted_sessions == [session_id]


@pytest.mark.asyncio
async def test_session_not_found(client: AsyncClient, auth_headers: dict[str, str]):
    res = await client.get("/api/v1/sessions/9999", headers=auth_headers)
    assert res.status_code == 404

