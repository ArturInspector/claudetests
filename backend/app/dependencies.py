from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import decode_access_token
from app.db import get_session
from app.models import User
from app.services.graph import GraphBuilderService, NullGraphBuilder
from app.services.llm.base import LLMClient, NullLLM
from app.services.llm.openrouter import OpenRouterLLM
from app.services.rag import NullRAG, RAGService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Validate the bearer token and return the associated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_exception

    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception

    user = await session.get(User, int(subject))
    if user is None:
        raise credentials_exception

    return user


@lru_cache
def _cached_llm(settings_signature: tuple) -> LLMClient:
    settings = get_settings()
    if not settings.openrouter_api_key:
        return NullLLM()
    return OpenRouterLLM(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        fallback_model=settings.openrouter_fallback_model,
        embedding_model=settings.openrouter_embedding_model,
    )


def get_llm_client(settings=Depends(get_settings)) -> LLMClient:
    """Provide LLM client; returns a no-op client when key is missing."""
    signature = (
        settings.openrouter_api_key,
        settings.openrouter_model,
        settings.openrouter_fallback_model,
        settings.openrouter_embedding_model,
    )
    return _cached_llm(signature)


def get_rag_service(
    llm: LLMClient = Depends(get_llm_client),
    settings=Depends(get_settings),
):
    """Provide RAG service backed by ChromaDB; falls back to no-op."""
    try:
        return RAGService(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
            collection_prefix=settings.chromadb_collection_prefix,
            llm=llm,
        )
    except Exception:  # pragma: no cover - best-effort path
        return NullRAG()


@lru_cache
def _cached_graph_builder(settings_signature: tuple, llm: LLMClient) -> GraphBuilderService:
    settings = get_settings()
    try:
        builder = GraphBuilderService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm=llm,
        )
        return builder
    except Exception:
        return NullGraphBuilder()


async def get_graph_builder(
    llm: LLMClient = Depends(get_llm_client),
    settings=Depends(get_settings),
) -> GraphBuilderService:
    import logging
    log = logging.getLogger(__name__)
    
    signature = (settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    builder = _cached_graph_builder(signature, llm)
    
    if isinstance(builder, NullGraphBuilder):
        log.warning("Using NullGraphBuilder, graph operations disabled")
        return builder
    
    try:
        await builder.connect()
        log.info("GraphBuilderService connected to Neo4j at %s", settings.neo4j_uri)
    except Exception as exc:
        log.error("Failed to connect GraphBuilderService to Neo4j: %s", exc)
        return NullGraphBuilder()
    
    return builder

