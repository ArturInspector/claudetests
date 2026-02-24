from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class NullGraphBuilder:
    async def connect(self) -> None:
        log.warning("Using NullGraphBuilder - Neo4j unavailable")

    async def close(self) -> None:
        pass

    async def ensure_user_exists(self, user_id: str) -> None:
        pass

    async def get_user_graph(self, user_id: str, depth: int = 2) -> dict[str, Any]:
        return {"concepts": [], "knowledge": [], "relationships": []}

    async def extract_concepts(
        self,
        user_id: str,
        question: str,
        answer: str,
        topic: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        return []

    async def build_relationships(
        self,
        user_id: str,
        concepts: list[dict[str, Any]],
        answer: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        return []

    async def calculate_blind_zones(
        self,
        user_id: str,
        topic: str | None = None,
        min_mastery_threshold: float = 0.7,
    ) -> dict[str, Any]:
        return {
            "unexplored_branches": [],
            "weak_connections": [],
            "missing_prerequisites": [],
            "total_blind_zones": 0,
        }

    async def get_learning_progress(self, user_id: str, topic: str | None = None) -> dict[str, Any]:
        return {
            "total_concepts": 0,
            "mastered": 0,
            "partial": 0,
            "weak": 0,
            "average_mastery": 0.0,
        }

    async def health_check(self) -> bool:
        return False
