from __future__ import annotations

import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import LLMClient

log = logging.getLogger(__name__)


class OpenRouterLLM(LLMClient):
    """OpenRouter-based LLM client with simple fallback."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_model: str | None,
        embedding_model: str,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.embedding_model = embedding_model
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=4), stop=stop_after_attempt(2))
    async def _post(self, path: str, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload, headers=self._headers())
            response.raise_for_status()
            return response

    async def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "You are a concise learning coach."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 512,
        }
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        for model_name in models_to_try:
            payload["model"] = model_name
            try:
                response = await self._post("/chat/completions", payload)
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as exc:  # pragma: no cover - best-effort fallback
                log.warning("LLM call failed for model %s: %s", model_name, exc)
                continue

        return "LLM unavailable (all providers failed)."

    async def embed(self, text: str) -> list[float]:
        payload = {"model": self.embedding_model, "input": text}
        try:
            response = await self._post("/embeddings", payload)
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as exc:  # pragma: no cover - graceful degradation
            log.warning("Embedding request failed: %s", exc)
            # deterministic fallback
            h = abs(hash(text))
            return [(h % (i + 13)) / 100.0 for i in range(8)]

