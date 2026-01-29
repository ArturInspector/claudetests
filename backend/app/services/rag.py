from __future__ import annotations

import logging

import chromadb

from app.services.llm.base import LLMClient

log = logging.getLogger(__name__)


class RAGService:
    """ChromaDB-backed retrieval for past answers."""

    def __init__(self, host: str, port: int, collection_prefix: str, llm: LLMClient):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection_prefix = collection_prefix
        self._llm = llm

    def _collection_name(self, user_id: int) -> str:
        return f"{self._collection_prefix}-{user_id}-sessions"

    def _collection(self, user_id: int):
        return self._client.get_or_create_collection(self._collection_name(user_id))

    async def index_answer(
        self,
        *,
        user_id: int,
        session_id: int,
        iteration_id: int,
        text: str,
        metadata: dict,
    ) -> None:
        try:
            embedding = await self._llm.embed(text)
            coll = self._collection(user_id)
            coll.add(
                ids=[f"{session_id}:{iteration_id}"],
                documents=[text],
                metadatas=[{**metadata, "session_id": session_id, "iteration_id": iteration_id}],
                embeddings=[embedding],
            )
        except Exception as exc:  # pragma: no cover - best-effort path
            log.warning("Failed to index answer in Chroma: %s", exc)

    async def similar_context(self, *, user_id: int, text: str, limit: int = 3) -> list[str]:
        try:
            coll = self._collection(user_id)
            embedding = await self._llm.embed(text)
            result = coll.query(query_embeddings=[embedding], n_results=limit)
            return result.get("documents", [[]])[0] or []
        except Exception as exc:  # pragma: no cover - degrade gracefully
            log.warning("Failed to query Chroma: %s", exc)
            return []

    def delete_session(self, *, user_id: int, session_id: int) -> None:
        try:
            coll = self._collection(user_id)
            coll.delete(where={"session_id": session_id})
        except Exception as exc:  # pragma: no cover - best-effort
            log.warning("Failed to delete session vectors: %s", exc)


class NullRAG(RAGService):
    """No-op RAG used when Chroma is unavailable."""

    def __init__(self) -> None:
        pass

    async def index_answer(self, **_: dict) -> None:
        return None

    async def similar_context(self, **_: dict) -> list[str]:
        return []

    def delete_session(self, **_: dict) -> None:
        return None

