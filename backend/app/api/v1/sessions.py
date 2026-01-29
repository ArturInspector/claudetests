from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_llm_client, get_rag_service
from app.db import get_session
from app.models import Session, User
from app.schemas.session import (
    AnswerRequest,
    AnswerResponse,
    IterationRead,
    SessionCreate,
    SessionDetail,
    SessionRead,
    SessionSummary,
)
from app.services import prompts
from app.services.llm.base import LLMClient
from app.services.rag import RAGService
from app.services.session import (
    append_iteration,
    create_session,
    delete_session,
    get_session_with_iterations,
    list_sessions,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _get_session_or_404(
    db: AsyncSession, user_id: int, session_id: int
) -> Session:
    session_obj = await get_session_with_iterations(db, user_id=user_id, session_id=session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session_obj


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Start a new learning session."""
    session_obj = await create_session(db, user_id=current_user.id, payload=payload)
    return SessionRead.model_validate(session_obj)


@router.get("", response_model=list[SessionSummary])
async def list_user_sessions(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List sessions for the current user."""
    sessions = await list_sessions(db, user_id=current_user.id)
    return [
        SessionSummary.model_validate(
            {**SessionRead.model_validate(s).model_dump(), "iteration_count": len(s.iterations)}
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return session with iterations."""
    session_obj = await _get_session_or_404(db, current_user.id, session_id)
    return SessionDetail.model_validate(session_obj)


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    session_id: int,
    payload: AnswerRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
    rag: RAGService = Depends(get_rag_service),
):
    """Submit an answer for an iteration, generate feedback, and index it."""
    session_obj = await _get_session_or_404(db, current_user.id, session_id)

    similar = await rag.similar_context(user_id=current_user.id, text=payload.answer, limit=3)
    prompt = prompts.build_feedback_prompt(
        question=payload.question, answer=payload.answer, context=similar
    )
    feedback = await llm.generate(prompt)

    iteration = await append_iteration(
        db,
        session_obj=session_obj,
        question=payload.question,
        answer=payload.answer,
        feedback=feedback,
    )

    await rag.index_answer(
        user_id=current_user.id,
        session_id=session_obj.id,
        iteration_id=iteration.id,
        text=payload.answer,
        metadata={"topic": session_obj.topic, "number": iteration.number},
    )

    return AnswerResponse(
        iteration=IterationRead.model_validate(iteration),
        similar_context=similar,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(
    session_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_service),
):
    """Delete a session and associated vectors."""
    session_obj = await _get_session_or_404(db, current_user.id, session_id)
    await delete_session(db, session_obj=session_obj)
    rag.delete_session(user_id=current_user.id, session_id=session_id)
    return None

