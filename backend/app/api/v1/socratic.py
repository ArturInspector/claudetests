from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    get_graph_builder,
    get_llm_client,
    get_rag_service,
)
from app.models import User
from app.schemas import SocraticAnalyzeRequest, SocraticAnalyzeResponse
from app.services.analysis import analyze_answer_socratic
from app.services.graph_builder import GraphBuilderService
from app.services.llm.base import LLMClient
from app.services.rag import RAGService

router = APIRouter(prefix="/socratic", tags=["socratic"])


@router.post("/analyze", response_model=SocraticAnalyzeResponse)
async def analyze_answer(
    payload: SocraticAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
    rag: RAGService = Depends(get_rag_service),
    graph: GraphBuilderService = Depends(get_graph_builder),
):
    """Hybrid сократический анализ ответа."""
    return await analyze_answer_socratic(
        llm=llm,
        rag=rag,
        graph=graph,
        user_id=current_user.id,
        question=payload.question,
        answer=payload.answer,
        topic=payload.topic or "",
        session_id=str(payload.session_id or ""),
        required_terms=payload.required_terms,
        mode=payload.mode or "practice",
    )

