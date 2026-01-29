from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Iteration, Session
from app.schemas.session import SessionCreate


async def load_prior_knowledge(graph_builder, user_id: str, topic: str) -> dict:
    await graph_builder.ensure_user_exists(user_id)
    
    user_graph = await graph_builder.get_user_graph(user_id=user_id, depth=2)
    
    if not user_graph or not user_graph.get("concepts"):
        return {
            "has_prior_knowledge": False,
            "related_concepts": [],
            "mastered_concepts": [],
            "weak_areas": [],
            "average_mastery": 0.0,
        }
    
    concepts = user_graph.get("concepts", [])
    knowledge = user_graph.get("knowledge", [])
    
    mastery_map = {}
    for k in knowledge:
        concept_id = k.get("concept_id")
        if concept_id:
            mastery_map[concept_id] = k.get("mastery_level", 0.0)
    
    topic_lower = topic.lower()
    related_concepts = [
        c for c in concepts 
        if topic_lower in c.get("name", "").lower() or topic_lower in c.get("topic", "").lower()
    ]
    
    mastered = [
        c for c in concepts 
        if mastery_map.get(c.get("concept_id"), 0.0) >= 0.7
    ]
    
    weak = [
        c for c in concepts 
        if 0.0 < mastery_map.get(c.get("concept_id"), 0.0) < 0.5
    ]
    
    total_mastery = sum(mastery_map.values())
    avg_mastery = total_mastery / len(mastery_map) if mastery_map else 0.0
    
    return {
        "has_prior_knowledge": len(related_concepts) > 0,
        "related_concepts": [c.get("name") for c in related_concepts[:5]],
        "mastered_concepts": [c.get("name") for c in mastered[:5]],
        "weak_areas": [c.get("name") for c in weak[:5]],
        "average_mastery": round(avg_mastery, 2),
        "total_concepts": len(concepts),
    }


async def create_session_with_context(
    db: AsyncSession,
    graph_builder,
    user_id: int,
    payload: SessionCreate,
) -> tuple[Session, dict]:
    prior_knowledge = await load_prior_knowledge(
        graph_builder=graph_builder,
        user_id=str(user_id),
        topic=payload.topic,
    )
    
    session = Session(topic=payload.topic, level=payload.level, user_id=user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session, prior_knowledge


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

