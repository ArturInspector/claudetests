from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    """Return service health with graceful degradation."""
    settings = get_settings()
    checks: dict[str, str] = {}
    status = "ok"

    try:
        await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # pragma: no cover - best-effort logging
        status = "degraded"
        checks["postgres"] = f"error: {exc}"

    return {
        "status": status,
        "environment": settings.environment,
        "checks": checks,
    }

