from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    payload = {"email": "new@example.com", "password": "password123"}
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == payload["email"]

    res_login = await client.post("/api/v1/auth/login", json=payload)
    assert res_login.status_code == 200
    assert res_login.json()["access_token"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 400
    assert res.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    payload = {"email": "wrong@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    res = await client.post(
        "/api/v1/auth/login", json={"email": payload["email"], "password": "badpass"}
    )
    assert res.status_code == 401

