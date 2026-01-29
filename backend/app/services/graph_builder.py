"""
Knowledge Graph Builder Service.

Отвечает за:
- Подключение к Neo4j
- Извлечение концептов из ответов пользователя
- Построение связей между концептами
- Вычисление blind zones
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import Settings

log = logging.getLogger(__name__)


class GraphBuilderService:
    """
    Сервис для управления knowledge graph в Neo4j.
    
    Архитектура:
    - Каждый пользователь имеет свой подграф (изолированный по user_id)
    - Концепты связаны через RELATES_TO, PREREQUISITE_FOR
    - Прогресс отслеживается через KNOWS relationship с mastery_level
    """

    def __init__(self, uri: str, user: str, password: str):
        """
        Инициализация подключения к Neo4j.
        
        Args:
            uri: Neo4j connection URI (bolt://...)
            user: Username для аутентификации
            password: Пароль
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = None

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

