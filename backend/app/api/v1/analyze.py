from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_llm_client
from app.db import get_session
from app.models import User
from app.services import prompts
from app.services.llm.base import LLMClient
from app.services.session import get_session_with_iterations

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/{session_id}")
async def analyze_session(
    session_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
):
    """Generate a progress summary for the session using the LLM."""
    session_obj = await get_session_with_iterations(db, user_id=current_user.id, session_id=session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    prompt = prompts.build_session_summary_prompt(session_obj.topic, session_obj.iterations)
    summary = await llm.generate(prompt)
    return {"session_id": session_id, "summary": summary}

