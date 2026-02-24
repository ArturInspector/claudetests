from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncDriver, AsyncSession

log = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    def session(self) -> AsyncSession:
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver.session()

    async def health_check(self) -> bool:
        try:
            if not self._driver:
                return False
            await self._driver.verify_connectivity()
            return True
        except Exception as exc:
            log.warning("Neo4j health check failed: %s", exc)
            return False

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            log.info("Neo4j connection closed")
