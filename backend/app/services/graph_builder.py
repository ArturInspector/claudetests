"""
Knowledge Graph Builder Service.

Отвечает за:
- Подключение к Neo4j
- Извлечение концептов из ответов пользователя
- Построение связей между концептами
- Вычисление blind zones
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import Settings
from app.services.llm.base import LLMClient

log = logging.getLogger(__name__)


class GraphBuilderService:
    """
    Сервис для управления knowledge graph в Neo4j.
    
    Архитектура:
    - Каждый пользователь имеет свой подграф (изолированный по user_id)
    - Концепты связаны через RELATES_TO, PREREQUISITE_FOR
    - Прогресс отслеживается через KNOWS relationship с mastery_level
    """

    def __init__(self, uri: str, user: str, password: str, llm: LLMClient | None = None):
        """
        Инициализация подключения к Neo4j.
        
        Args:
            uri: Neo4j connection URI (bolt://...)
            user: Username для аутентификации
            password: Пароль
            llm: LLM client для извлечения концептов
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = None
        self._llm = llm

    async def connect(self) -> None:
        """Установить соединение с Neo4j."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            # Проверяем подключение
            await self._driver.verify_connectivity()
            log.info("Neo4j connection established: %s", self._uri)
        except (ServiceUnavailable, AuthError) as exc:
            log.error("Failed to connect to Neo4j: %s", exc)
            raise

    async def close(self) -> None:
        """Закрыть соединение с Neo4j."""
        if self._driver:
            await self._driver.close()
            log.info("Neo4j connection closed")

    def _session(self) -> AsyncSession:
        """Создать новую сессию для выполнения запросов."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver.session()

    async def ensure_user_exists(self, user_id: str) -> None:
        """
        Убедиться что узел User существует в графе.
        
        Args:
            user_id: UUID пользователя из PostgreSQL
        """
        async with self._session() as session:
            await session.run(
                """
                MERGE (u:User {user_id: $user_id})
                ON CREATE SET
                    u.created_at = datetime(),
                    u.total_sessions = 0
                """,
                user_id=user_id,
            )

    async def get_user_graph(self, user_id: str, depth: int = 2) -> dict[str, Any]:
        """
        Получить граф знаний пользователя.
        
        Args:
            user_id: UUID пользователя
            depth: Глубина обхода связей (по умолчанию 2)
            
        Returns:
            Dict с узлами (concepts) и связями (relationships)
        """
        async with self._session() as session:
            result = await session.run(
                """
                MATCH path = (u:User {user_id: $user_id})-[k:KNOWS]->(c:Concept)
                OPTIONAL MATCH (c)-[r:RELATES_TO*1..$depth]->(related:Concept)
                RETURN 
                    collect(DISTINCT c) as concepts,
                    collect(DISTINCT k) as knowledge_rels,
                    collect(DISTINCT r) as concept_rels
                """,
                user_id=user_id,
                depth=depth,
            )
            record = await result.single()
            
            if not record:
                return {"concepts": [], "knowledge": [], "relationships": []}
            
            return {
                "concepts": [dict(c) for c in record["concepts"]],
                "knowledge": [dict(k) for k in record["knowledge_rels"]],
                "relationships": [dict(r) for r in record["concept_rels"] if r],
            }

    async def health_check(self) -> bool:
        """
        Проверка здоровья подключения к Neo4j.
        
        Returns:
            True если соединение работает
        """
        try:
            if not self._driver:
                return False
            await self._driver.verify_connectivity()
            return True
        except Exception as exc:
            log.warning("Neo4j health check failed: %s", exc)
            return False

    async def extract_concepts(
        self,
        user_id: str,
        question: str,
        answer: str,
        topic: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """
        Извлечь концепты из ответа пользователя с помощью LLM.
        
        Args:
            user_id: UUID пользователя
            question: Вопрос который задавался
            answer: Ответ пользователя
            topic: Тема сессии
            session_id: UUID сессии
            
        Returns:
            Список концептов с их характеристиками
        """
        if not self._llm:
            log.warning("LLM not available, skipping concept extraction")
            return []

        prompt = self._build_extraction_prompt(question, answer, topic)
        
        try:
            response = await self._llm.generate(
                prompt=prompt,
                system="You are a concept extraction system. Return only valid JSON.",
            )
            
            # Парсим JSON ответ
            concepts_data = self._parse_llm_response(response)
            
            # Сохраняем концепты в Neo4j
            concepts = []
            for concept_data in concepts_data:
                concept = await self._create_or_update_concept(
                    user_id=user_id,
                    session_id=session_id,
                    concept_data=concept_data,
                    topic=topic,
                )
                if concept:
                    concepts.append(concept)
            
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

    def _build_extraction_prompt(self, question: str, answer: str, topic: str) -> str:
        """
        Построить prompt для LLM чтобы извлечь концепты.
        
        Structured prompt с четкой схемой ответа.
        """
        return f"""
Extract technical concepts from the user's answer below.

**Context:**
- Topic: {topic}
- Question: {question}

**User's Answer:**
{answer}

**Task:**
Identify key technical concepts mentioned or implied in the answer.
For each concept, provide:
1. name: short name (2-5 words)
2. description: brief explanation (1 sentence)
3. confidence: how clearly user understands it (0.0-1.0)
4. mentioned_explicitly: true if directly mentioned, false if implied

**Output Format (JSON only, no markdown):**
{{
  "concepts": [
    {{
      "name": "concept name",
      "description": "brief explanation",
      "confidence": 0.7,
      "mentioned_explicitly": true
    }}
  ]
}}

Return ONLY the JSON, no additional text.
""".strip()

    def _parse_llm_response(self, response: str) -> list[dict[str, Any]]:
        """
        Парсить JSON ответ от LLM.
        
        Обрабатывает случаи когда LLM возвращает markdown или лишний текст.
        """
        try:
            # Убираем markdown code blocks если есть
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Находим JSON между ```json и ```
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]
            
            data = json.loads(cleaned)
            return data.get("concepts", [])
        except json.JSONDecodeError as exc:
            log.error("Failed to parse LLM response as JSON: %s", exc)
            return []

    async def _create_or_update_concept(
        self,
        user_id: str,
        session_id: str,
        concept_data: dict[str, Any],
        topic: str,
    ) -> dict[str, Any] | None:
        """
        Создать или обновить концепт в Neo4j.
        
        Args:
            user_id: UUID пользователя
            session_id: UUID сессии
            concept_data: Данные концепта от LLM
            topic: Тема
            
        Returns:
            Созданный/обновлённый концепт или None при ошибке
        """
        concept_id = f"concept-{uuid4()}"
        name = concept_data.get("name", "Unknown")
        description = concept_data.get("description", "")
        confidence = float(concept_data.get("confidence", 0.5))
        
        try:
            async with self._session() as session:
                # Создаём/обновляем концепт
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


class NullGraphBuilder(GraphBuilderService):
    """No-op граф билдер для случаев когда Neo4j недоступен."""

    def __init__(self) -> None:
        pass

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

    async def health_check(self) -> bool:
        return False


def create_graph_builder(settings: Settings) -> GraphBuilderService:
    """
    Factory для создания GraphBuilderService.
    
    Args:
        settings: Application settings
        
    Returns:
        GraphBuilderService или NullGraphBuilder если Neo4j недоступен
    """
    try:
        return GraphBuilderService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
    except Exception as exc:
        log.error("Failed to create GraphBuilderService: %s", exc)
        return NullGraphBuilder()

