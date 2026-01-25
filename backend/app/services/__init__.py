"""Service layer exports."""

from .llm.base import LLMClient, NullLLM
from .llm.openrouter import OpenRouterLLM
from .prompts import build_feedback_prompt, build_session_summary_prompt
from .rag import NullRAG, RAGService
from .session import (
    append_iteration,
    create_session,
    delete_session,
    get_session_with_iterations,
    list_sessions,
)

__all__ = [
    "LLMClient",
    "NullLLM",
    "OpenRouterLLM",
    "RAGService",
    "NullRAG",
    "create_session",
    "list_sessions",
    "get_session_with_iterations",
    "append_iteration",
    "delete_session",
    "build_feedback_prompt",
    "build_session_summary_prompt",
]

