from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.dependencies import (
    get_current_user,
    get_graph_builder,
    get_llm_client,
    get_rag_service,
)
from app.models import Message, Session, User
from app.schemas import SocraticAnalyzeRequest, SocraticAnalyzeResponse
from app.services.analysis import analyze_answer_socratic
from app.services.graph import GraphBuilderService
from app.services.llm.base import LLMClient
from app.services.rag import RAGService
from app.services.session import create_session
from app.schemas.session import SessionCreate

router = APIRouter(prefix="/socratic", tags=["socratic"])


def _session_dialogue_context(session_obj: Session) -> tuple[list[dict], list[dict]]:
    """Build dialogue_history and prior_gaps from session messages for adaptive context."""
    if not getattr(session_obj, "messages", None):
        return [], []
    sorted_messages = sorted(session_obj.messages, key=lambda m: m.timestamp)
    dialogue_history = [
        {"role": m.role, "content": m.content[:500] + ("..." if len(m.content) > 500 else "")}
        for m in sorted_messages
    ]
    prior_gaps: list[dict] = []
    for m in sorted_messages:
        if m.role == "assistant" and m.analysis_json:
            analysis = m.analysis_json.get("analysis") or {}
            for g in analysis.get("gaps") or []:
                prior_gaps.append(g)
    return dialogue_history, prior_gaps


@router.post("/analyze", response_model=SocraticAnalyzeResponse)
async def analyze_answer(
    payload: SocraticAnalyzeRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
    rag: RAGService = Depends(get_rag_service),
    graph: GraphBuilderService = Depends(get_graph_builder),
):
    """Hybrid сократический анализ ответа с сохранением в messages и учётом контекста сессии."""
    session_obj = None
    dialogue_history: list[dict] = []
    prior_gaps: list[dict] = []

    if payload.session_id:
        result = await db.execute(
            select(Session)
            .where(
                Session.id == int(payload.session_id),
                Session.user_id == current_user.id,
            )
            .options(selectinload(Session.messages))
        )
        session_obj = result.scalar_one_or_none()
        if session_obj:
            dialogue_history, prior_gaps = _session_dialogue_context(session_obj)

    if not session_obj and payload.topic:
        session_obj = await create_session(
            db,
            user_id=current_user.id,
            payload=SessionCreate(topic=payload.topic, level=None),
        )

    result = await analyze_answer_socratic(
        llm=llm,
        rag=rag,
        graph=graph,
        user_id=current_user.id,
        question=payload.question,
        answer=payload.answer,
        topic=payload.topic or "",
        session_id=str(session_obj.id) if session_obj else "",
        required_terms=payload.required_terms,
        mode=payload.mode or "practice",
        dialogue_history=dialogue_history,
        prior_gaps=prior_gaps,
    )
    
    # Сохраняем сообщения если есть сессия
    if session_obj:
        # Сохраняем сообщение пользователя
        user_message = Message(
            session_id=session_obj.id,
            role="user",
            content=payload.answer,
            analysis_json=None,
        )
        db.add(user_message)
        
        # Сохраняем сообщение ассистента
        selected_question = result.get("socratic", {}).get("selected_question", "")
        assistant_message = Message(
            session_id=session_obj.id,
            role="assistant",
            content=selected_question,
            analysis_json=result,
        )
        db.add(assistant_message)
        
        await db.commit()
    
    return result


