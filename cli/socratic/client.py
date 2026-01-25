from __future__ import annotations

from typing import Any

import httpx


class APIClient:
    """Thin HTTP client for the Socratic API."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(timeout=15)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, *, email: str, password: str) -> str:
        resp = self._client.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def start_session(self, *, topic: str, level: str | None) -> dict[str, Any]:
        resp = self._client.post(
            f"{self.base_url}/sessions",
            json={"topic": topic, "level": level},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def list_sessions(self) -> list[dict[str, Any]]:
        resp = self._client.get(f"{self.base_url}/sessions", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def answer(
        self, *, session_id: int, question: str, answer: str
    ) -> dict[str, Any]:
        resp = self._client.post(
            f"{self.base_url}/sessions/{session_id}/answer",
            json={"question": question, "answer": answer},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def analyze(self, *, session_id: int) -> dict[str, Any]:
        resp = self._client.post(
            f"{self.base_url}/analyze/{session_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def session_detail(self, *, session_id: int) -> dict[str, Any]:
        resp = self._client.get(
            f"{self.base_url}/sessions/{session_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

