from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncSession

log = logging.getLogger(__name__)


class QueryRepository:
    async def get_user_graph(self, session: AsyncSession, user_id: str) -> dict[str, Any]:
        log.info("Fetching user graph for user_id=%s", user_id)
        result = await session.run(
            """
            MATCH path = (u:User {user_id: $user_id})-[k:KNOWS]->(c:Concept)
            OPTIONAL MATCH (c)-[r:RELATES_TO*1..2]->(related:Concept)
            RETURN 
                collect(DISTINCT c) as concepts,
                collect(DISTINCT k) as knowledge_rels,
                collect(DISTINCT r) as concept_rels
            """,
            user_id=user_id,
        )
        record = await result.single()

        if not record:
            log.info("No graph data found for user_id=%s", user_id)
            return {"concepts": [], "knowledge": [], "relationships": []}

        concepts_count = len(record["concepts"])
        log.info("Fetched %d concepts for user_id=%s", concepts_count, user_id)

        return {
            "concepts": [dict(c) for c in record["concepts"]],
            "knowledge": [dict(k) for k in record["knowledge_rels"]],
            "relationships": [dict(r) for r in record["concept_rels"] if r],
        }

    async def find_unexplored_branches(
        self,
        session: AsyncSession,
        user_id: str,
        topic: str | None,
        threshold: float,
    ) -> list[dict[str, Any]]:
        topic_filter = "AND c1.topic = $topic" if topic else ""

        result = await session.run(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[k:KNOWS]->(c1:Concept)
            WHERE k.mastery_level >= $threshold {topic_filter}
            
            MATCH (c1)-[r:RELATES_TO]->(c2:Concept)
            WHERE NOT EXISTS {{
                MATCH (u)-[:KNOWS]->(c2)
            }}
            
            RETURN DISTINCT
                c2.concept_id as concept_id,
                c2.name as name,
                c2.description as description,
                c1.name as known_concept,
                r.relationship_type as relationship_type,
                r.strength as connection_strength
            ORDER BY r.strength DESC
            LIMIT 10
            """,
            user_id=user_id,
            threshold=threshold,
            topic=topic,
        )

        return [dict(record) async for record in result]

    async def find_weak_connections(
        self,
        session: AsyncSession,
        user_id: str,
        topic: str | None,
        threshold: float,
    ) -> list[dict[str, Any]]:
        topic_filter = "AND c.topic = $topic" if topic else ""

        result = await session.run(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[k:KNOWS]->(c:Concept)
            WHERE k.mastery_level < $threshold
            AND k.mastery_level > 0.0
            {topic_filter}
            
            RETURN
                c.concept_id as concept_id,
                c.name as name,
                c.description as description,
                k.mastery_level as current_mastery,
                k.confidence as confidence,
                k.interaction_count as times_reviewed
            ORDER BY k.mastery_level ASC
            LIMIT 10
            """,
            user_id=user_id,
            threshold=threshold,
            topic=topic,
        )

        return [dict(record) async for record in result]

    async def find_missing_prerequisites(
        self,
        session: AsyncSession,
        user_id: str,
        topic: str | None,
    ) -> list[dict[str, Any]]:
        topic_filter = "AND c2.topic = $topic" if topic else ""

        result = await session.run(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[k2:KNOWS]->(c2:Concept)
            MATCH (c1:Concept)-[p:PREREQUISITE_FOR]->(c2)
            WHERE NOT EXISTS {{
                MATCH (u)-[k1:KNOWS]->(c1)
                WHERE k1.mastery_level >= p.required_mastery
            }}
            {topic_filter}
            
            RETURN DISTINCT
                c1.concept_id as missing_concept_id,
                c1.name as missing_concept_name,
                c1.description as missing_concept_description,
                c2.name as dependent_concept,
                p.required_mastery as required_mastery_level
            ORDER BY p.required_mastery DESC
            LIMIT 10
            """,
            user_id=user_id,
            topic=topic,
        )

        return [dict(record) async for record in result]

    async def get_learning_progress(
        self,
        session: AsyncSession,
        user_id: str,
        topic: str | None,
    ) -> dict[str, Any]:
        topic_filter = "AND c.topic = $topic" if topic else ""

        result = await session.run(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[k:KNOWS]->(c:Concept)
            WHERE 1=1 {topic_filter}
            
            WITH
                count(c) as total_concepts,
                sum(CASE WHEN k.mastery_level >= 0.8 THEN 1 ELSE 0 END) as mastered,
                sum(CASE WHEN k.mastery_level >= 0.5 AND k.mastery_level < 0.8 THEN 1 ELSE 0 END) as partial,
                sum(CASE WHEN k.mastery_level < 0.5 THEN 1 ELSE 0 END) as weak,
                avg(k.mastery_level) as avg_mastery
            
            RETURN
                total_concepts,
                mastered,
                partial,
                weak,
                avg_mastery
            """,
            user_id=user_id,
            topic=topic,
        )

        record = await result.single()
        if record:
            return {
                "total_concepts": record["total_concepts"] or 0,
                "mastered": record["mastered"] or 0,
                "partial": record["partial"] or 0,
                "weak": record["weak"] or 0,
                "average_mastery": round(record["avg_mastery"] or 0.0, 2),
            }

        return {
            "total_concepts": 0,
            "mastered": 0,
            "partial": 0,
            "weak": 0,
            "average_mastery": 0.0,
        }
