from __future__ import annotations

import os
from typing import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.dependencies import get_llm_client, get_rag_service
from app.main import create_app
from app.services.llm.base import LLMClient
from app.services.rag import RAGService

from .fakes import FakeLLM, FakeRAG


@pytest.fixture(scope="session", autouse=True)
def configure_settings(tmp_path_factory: pytest.TempPathFactory) -> None:
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["JWT_SECRET"] = "test-secret"
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def fake_llm() -> LLMClient:
    return FakeLLM()


@pytest.fixture(scope="session")
def fake_rag() -> FakeRAG:
    return FakeRAG()


@pytest.fixture(scope="session")
def app(fake_llm: LLMClient, fake_rag: FakeRAG):
    app = create_app()
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    app.dependency_overrides[get_rag_service] = lambda: fake_rag
    return app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, lifespan="on")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    email = "user@example.com"
    password = "pass12345"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

