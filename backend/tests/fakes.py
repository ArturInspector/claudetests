from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.llm.base import LLMClient
from app.services.rag import RAGService


class FakeLLM(LLMClient):
    """Deterministic LLM stub for tests."""

    async def generate(self, prompt: str, system: str | None = None) -> str:
        return f"fake-response:{prompt[:32]}"

    async def embed(self, text: str) -> list[float]:
        # Stable small vector for predictable tests
        return [float(len(text) % 5), 1.0, 2.0]


@dataclass
class FakeRAG(RAGService):
    """In-memory RAG stub that records interactions."""

    similar: list[str] = field(default_factory=lambda: ["ctx-1", "ctx-2"])
    indexed: list[dict[str, Any]] = field(default_factory=list)
    deleted_sessions: list[int] = field(default_factory=list)

    def __init__(self) -> None:
        # skip parent init; no external client
        pass

    async def index_answer(
        self,
        *,
        user_id: int,
        session_id: int,
        iteration_id: int,
        text: str,
        metadata: dict,
    ) -> None:
        self.indexed.append(
            {
                "user_id": user_id,
                "session_id": session_id,
                "iteration_id": iteration_id,
                "text": text,
                "metadata": metadata,
            }
        )

    async def similar_context(self, *, user_id: int, text: str, limit: int = 3) -> list[str]:
        return self.similar[:limit]

    def delete_session(self, *, user_id: int, session_id: int) -> None:
        self.deleted_sessions.append(session_id)

