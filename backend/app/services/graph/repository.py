from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from neo4j import AsyncSession

log = logging.getLogger(__name__)


class ConceptRepository:
    async def ensure_user_exists(self, session: AsyncSession, user_id: str) -> None:
        await session.run(
            """
            MERGE (u:User {user_id: $user_id})
            ON CREATE SET
                u.created_at = datetime(),
                u.total_sessions = 0
            """,
            user_id=user_id,
        )

    async def create_or_update_concept(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        concept_data: dict[str, Any],
        topic: str,
    ) -> dict[str, Any] | None:
        concept_id = f"concept-{uuid4()}"
        name = concept_data.get("name", "Unknown")
        description = concept_data.get("description", "")
        confidence = float(concept_data.get("confidence", 0.5))

        try:
            result = await session.run(
                """
                MERGE (c:Concept {name: $name, topic: $topic})
                ON CREATE SET
                    c.concept_id = $concept_id,
                    c.description = $description,
                    c.first_seen_at = datetime(),
                    c.times_reviewed = 1
                ON MATCH SET
                    c.times_reviewed = c.times_reviewed + 1,
                    c.last_reviewed_at = datetime()
                
                WITH c
                MERGE (u:User {user_id: $user_id})
                MERGE (u)-[k:KNOWS]->(c)
                ON CREATE SET
                    k.mastery_level = $confidence,
                    k.confidence = $confidence,
                    k.last_interaction = datetime(),
                    k.interaction_count = 1
                ON MATCH SET
                    k.mastery_level = (k.mastery_level + $confidence) / 2,
                    k.confidence = $confidence,
                    k.last_interaction = datetime(),
                    k.interaction_count = k.interaction_count + 1
                
                RETURN c, k
                """,
                concept_id=concept_id,
                name=name,
                description=description,
                topic=topic,
                user_id=user_id,
                confidence=confidence,
            )

            record = await result.single()
            if record:
                concept_node = dict(record["c"])
                knows_rel = dict(record["k"])
                return {
                    **concept_node,
                    "mastery_level": knows_rel.get("mastery_level"),
                }

        except Exception as exc:
            log.error("Failed to create/update concept: %s", exc)

        return None

    async def create_relationship(
        self,
        session: AsyncSession,
        from_name: str,
        to_name: str,
        rel_type: str,
        strength: float,
        session_id: str,
    ) -> dict[str, Any] | None:
        try:
            result = await session.run(
                """
                MATCH (c1:Concept {name: $from_name})
                MATCH (c2:Concept {name: $to_name})
                WHERE c1 <> c2
                
                MERGE (c1)-[r:RELATES_TO {relationship_type: $rel_type}]->(c2)
                ON CREATE SET
                    r.strength = $strength,
                    r.discovered_in_session = $session_id,
                    r.created_at = datetime()
                ON MATCH SET
                    r.strength = (r.strength + $strength) / 2
                
                RETURN r, c1.name as from_name, c2.name as to_name
                """,
                from_name=from_name,
                to_name=to_name,
                rel_type=rel_type,
                strength=strength,
                session_id=session_id,
            )

            record = await result.single()
            if record:
                return {
                    "from": record["from_name"],
                    "to": record["to_name"],
                    "type": rel_type,
                    "strength": strength,
                }

        except Exception as exc:
            log.error("Failed to create relationship: %s", exc)

        return None

    async def ensure_session_exists(
        self,
        session: AsyncSession,
        session_id: str,
        topic: str,
    ) -> None:
        await session.run(
            """
            MERGE (s:Session {session_id: $session_id})
            ON CREATE SET
                s.topic = $topic,
                s.created_at = datetime()
            ON MATCH SET
                s.topic = $topic
            """,
            session_id=session_id,
            topic=topic,
        )

    async def link_concept_to_session(
        self,
        session: AsyncSession,
        concept_id: str,
        session_id: str,
    ) -> bool:
        try:
            await session.run(
                """
                MATCH (c:Concept {concept_id: $concept_id})
                MATCH (s:Session {session_id: $session_id})
                MERGE (c)-[r:DISCUSSED_IN]->(s)
                ON CREATE SET r.created_at = datetime()
                """,
                concept_id=concept_id,
                session_id=session_id,
            )
            return True
        except Exception as exc:
            log.error(
                "Failed to link concept %s to session %s: %s",
                concept_id,
                session_id,
                exc,
            )
            return False
