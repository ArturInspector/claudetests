from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Minimal interface for chat and embeddings."""

    async def generate(self, prompt: str, system: str | None = None) -> str: ...

    async def embed(self, text: str) -> list[float]: ...


class NullLLM(LLMClient):
    """No-op LLM used when API key is not configured."""

    async def generate(self, prompt: str, system: str | None = None) -> str:
        return "LLM unavailable (no API key configured)."

    async def embed(self, text: str) -> list[float]:
        # Stable deterministic vector length 8 based on hash
        h = abs(hash(text))
        return [(h % (i + 13)) / 100.0 for i in range(8)]

