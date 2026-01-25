from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Iteration, Session
from app.schemas.session import SessionCreate


async def create_session(db: AsyncSession, *, user_id: int, payload: SessionCreate) -> Session:
    session = Session(topic=payload.topic, level=payload.level, user_id=user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, *, user_id: int) -> list[Session]:
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .options(selectinload(Session.iterations))
        .order_by(Session.created_at.desc())
    )
    return list(result.scalars().all())


async def get_session_with_iterations(
    db: AsyncSession, *, user_id: int, session_id: int
) -> Session | None:
    return await db.scalar(
        select(Session)
        .where(Session.id == session_id, Session.user_id == user_id)
        .options(selectinload(Session.iterations))
    )


async def append_iteration(
    db: AsyncSession,
    *,
    session_obj: Session,
    question: str,
    answer: str,
    feedback: str | None,
) -> Iteration:
    next_number = await db.scalar(
        select(func.coalesce(func.max(Iteration.number), 0) + 1).where(
            Iteration.session_id == session_obj.id
        )
    )
    iteration = Iteration(
        session_id=session_obj.id,
        number=next_number or 1,
        question=question,
        answer=answer,
        feedback=feedback,
    )
    db.add(iteration)
    await db.commit()
    await db.refresh(iteration)
    await db.refresh(session_obj)
    return iteration


async def delete_session(db: AsyncSession, *, session_obj: Session) -> None:
    await db.delete(session_obj)
    await db.commit()

