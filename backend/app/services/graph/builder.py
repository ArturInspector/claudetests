from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.services.llm.base import LLMClient
from app.services.graph.client import Neo4jClient
from app.services.graph.llm_extractor import LLMExtractor
from app.services.graph.repository import ConceptRepository
from app.services.graph.queries import QueryRepository

log = logging.getLogger(__name__)


class GraphBuilderService:
    def __init__(self, uri: str, user: str, password: str, llm: LLMClient | None = None):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = None
        self._llm = llm
        self._client: Neo4jClient | None = None
        self._extractor: LLMExtractor | None = None
        self._concept_repo = ConceptRepository()
        self._query_repo = QueryRepository()

    async def connect(self) -> None:
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            await self._driver.verify_connectivity()
            self._client = Neo4jClient(self._driver)
            if self._llm:
                self._extractor = LLMExtractor(self._llm)
            log.info("Neo4j connection established: %s", self._uri)
        except (ServiceUnavailable, AuthError) as exc:
            log.error("Failed to connect to Neo4j: %s", exc)
            raise

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    async def health_check(self) -> bool:
        if not self._client:
            return False
        return await self._client.health_check()

    async def ensure_user_exists(self, user_id: str) -> None:
        if not self._client:
            raise RuntimeError("Neo4j client not initialized")
        async with self._client.session() as session:
            await self._concept_repo.ensure_user_exists(session, user_id)

    async def get_user_graph(self, user_id: str, depth: int = 2) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Neo4j client not initialized")
        async with self._client.session() as session:
            return await self._query_repo.get_user_graph(session, user_id)

    async def extract_concepts(
        self,
        user_id: str,
        question: str,
        answer: str,
        topic: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        if not self._llm or not self._extractor or not self._client:
            log.warning("LLM or client not available, skipping concept extraction")
            return []

        prompt = self._extractor.build_extraction_prompt(question, answer, topic)

        try:
            response = await self._llm.generate(
                prompt=prompt,
                system="You are a concept extraction system. Return only valid JSON.",
            )

            concepts_data = self._extractor.parse_llm_response(response)

            concepts = []
            async with self._client.session() as session:
                await self._concept_repo.ensure_session_exists(
                    session=session,
                    session_id=session_id,
                    topic=topic,
                )

                for concept_data in concepts_data:
                    concept = await self._concept_repo.create_or_update_concept(
                        session=session,
                        user_id=user_id,
                        session_id=session_id,
                        concept_data=concept_data,
                        topic=topic,
                    )
                    if concept:
                        concepts.append(concept)
                        concept_id = concept.get("concept_id")
                        if concept_id:
                            await self._concept_repo.link_concept_to_session(
                                session=session,
                                concept_id=concept_id,
                                session_id=session_id,
                            )

            log.info(
                "Extracted %d concepts for user %s in session %s",
                len(concepts),
                user_id,
                session_id,
            )
            return concepts

        except Exception as exc:
            log.error("Failed to extract concepts: %s", exc)
            return []

    async def build_relationships(
        self,
        user_id: str,
        concepts: list[dict[str, Any]],
        answer: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        if not self._llm or not self._extractor or not self._client or len(concepts) < 2:
            return []

        prompt = self._extractor.build_relationship_prompt(concepts, answer)

        try:
            response = await self._llm.generate(
                prompt=prompt,
                system="You are a knowledge graph relationship builder. Return only valid JSON.",
            )

            relationships_data = self._extractor.parse_relationships_response(response)

            relationships = []
            async with self._client.session() as session:
                for rel_data in relationships_data:
                    from_name = rel_data.get("from_concept")
                    to_name = rel_data.get("to_concept")
                    rel_type = rel_data.get("type", "similar")
                    strength = float(rel_data.get("strength", 0.5))

                    if not from_name or not to_name:
                        continue

                    rel = await self._concept_repo.create_relationship(
                        session=session,
                        from_name=from_name,
                        to_name=to_name,
                        rel_type=rel_type,
                        strength=strength,
                        session_id=session_id,
                    )
                    if rel:
                        relationships.append(rel)

            log.info(
                "Created %d relationships for user %s in session %s",
                len(relationships),
                user_id,
                session_id,
            )
            return relationships

        except Exception as exc:
            log.error("Failed to build relationships: %s", exc)
            return []

    async def calculate_blind_zones(
        self,
        user_id: str,
        topic: str | None = None,
        min_mastery_threshold: float = 0.7,
    ) -> dict[str, Any]:
        if not self._client:
            return {
                "unexplored_branches": [],
                "weak_connections": [],
                "missing_prerequisites": [],
                "total_blind_zones": 0,
            }

        try:
            async with self._client.session() as session:
                unexplored = await self._query_repo.find_unexplored_branches(
                    session, user_id, topic, min_mastery_threshold
                )

                weak = await self._query_repo.find_weak_connections(
                    session, user_id, topic, min_mastery_threshold
                )

                missing_prereqs = await self._query_repo.find_missing_prerequisites(
                    session, user_id, topic
                )

                return {
                    "unexplored_branches": unexplored,
                    "weak_connections": weak,
                    "missing_prerequisites": missing_prereqs,
                    "total_blind_zones": len(unexplored) + len(weak) + len(missing_prereqs),
                }

        except Exception as exc:
            log.error("Failed to calculate blind zones: %s", exc)
            return {
                "unexplored_branches": [],
                "weak_connections": [],
                "missing_prerequisites": [],
                "total_blind_zones": 0,
            }

    async def get_learning_progress(self, user_id: str, topic: str | None = None) -> dict[str, Any]:
        if not self._client:
            return {
                "total_concepts": 0,
                "mastered": 0,
                "partial": 0,
                "weak": 0,
                "average_mastery": 0.0,
            }

        try:
            async with self._client.session() as session:
                return await self._query_repo.get_learning_progress(session, user_id, topic)
        except Exception as exc:
            log.error("Failed to get learning progress: %s", exc)
            return {
                "total_concepts": 0,
                "mastered": 0,
                "partial": 0,
                "weak": 0,
                "average_mastery": 0.0,
            }

    async def get_session_graph(self, session_id: str) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Neo4j client not initialized")
        async with self._client.session() as session:
            return await self._query_repo.get_session_graph(session, session_id)
