"""Graph API endpoints для knowledge graph."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user, get_graph_builder
from app.models import User
from app.services.graph import GraphBuilderService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_user_graph(
    depth: int = 2,
    current_user: User = Depends(get_current_user),
    graph: GraphBuilderService = Depends(get_graph_builder),
):
    import logging
    log = logging.getLogger(__name__)
    
    user_id = str(current_user.id)
    log.info("GET /graph for user_id=%s, depth=%d", user_id, depth)
    
    try:
        user_graph = await graph.get_user_graph(user_id=user_id, depth=depth)
        
        response = {
            "user_id": current_user.id,
            "graph": user_graph,
            "stats": {
                "total_concepts": len(user_graph.get("concepts", [])),
                "total_relationships": len(user_graph.get("relationships", [])),
                "knowledge_edges": len(user_graph.get("knowledge", [])),
            }
        }
        log.info("Returning graph with %d concepts for user_id=%s", response["stats"]["total_concepts"], user_id)
        return response
    except Exception as exc:
        log.error("Failed to fetch graph for user_id=%s: %s", user_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch graph: {str(exc)}"
        )


@router.get("/concepts")
async def get_concepts(
    topic: str | None = None,
    min_mastery: float = 0.0,
    current_user: User = Depends(get_current_user),
    graph: GraphBuilderService = Depends(get_graph_builder),
):
    """
    Получить список концептов пользователя с фильтрацией.
    
    Args:
        topic: Фильтр по теме (опционально)
        min_mastery: Минимальный уровень mastery (0.0-1.0)
        current_user: Текущий пользователь
        graph: Graph builder сервис
    
    Returns:
        Список концептов с метаданными
    """
    user_id = str(current_user.id)
    
    try:
        user_graph = await graph.get_user_graph(user_id=user_id, depth=1)
        concepts = user_graph.get("concepts", [])
        knowledge = user_graph.get("knowledge", [])
        
        # Строим map mastery levels
        mastery_map = {}
        for k in knowledge:
            concept_name = k.get("end_node_name")
            if concept_name:
                mastery_map[concept_name] = k.get("mastery_level", 0.0)
        
        # Фильтруем концепты
        filtered = []
        for concept in concepts:
            name = concept.get("name", "")
            concept_topic = concept.get("topic", "")
            mastery = mastery_map.get(name, 0.0)
            
            # Применяем фильтры
            if topic and topic.lower() not in concept_topic.lower():
                continue
            
            if mastery < min_mastery:
                continue
            
            filtered.append({
                **concept,
                "mastery_level": mastery,
            })
        
        return {
            "concepts": filtered,
            "total": len(filtered),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch concepts: {str(exc)}"
        )


@router.get("/blind-zones")
async def get_blind_zones(
    current_user: User = Depends(get_current_user),
    graph: GraphBuilderService = Depends(get_graph_builder),
):
    """
    Получить blind zones пользователя.
    
    Blind zones — это:
    - Слабые концепты (mastery < 0.5)
    - Неизученные связанные концепты
    - Забытые концепты (давно не повторялись)
    
    Args:
        current_user: Текущий пользователь
        graph: Graph builder сервис
    
    Returns:
        Список blind zones с рекомендациями
    """
    user_id = str(current_user.id)
    
    try:
        user_graph = await graph.get_user_graph(user_id=user_id, depth=2)
        concepts = user_graph.get("concepts", [])
        knowledge = user_graph.get("knowledge", [])
        
        if not concepts:
            return {
                "blind_zones": [],
                "recommendations": ["Начните изучение — граф знаний пуст"],
            }
        
        # Строим map mastery levels
        mastery_map = {}
        for k in knowledge:
            concept_name = k.get("end_node_name")
            if concept_name:
                mastery_map[concept_name] = k.get("mastery_level", 0.0)
        
        blind_zones = []
        
        # 1. Слабые концепты
        weak_concepts = [
            {"name": name, "mastery": level, "type": "weak"}
            for name, level in mastery_map.items()
            if level < 0.5
        ]
        blind_zones.extend(weak_concepts)
        
        # 2. Неизученные концепты (times_reviewed <= 1)
        unexplored = [
            {"name": c.get("name"), "mastery": 0.0, "type": "unexplored"}
            for c in concepts
            if c.get("times_reviewed", 0) <= 1
        ]
        blind_zones.extend(unexplored)
        
        # Генерируем рекомендации
        recommendations = []
        if weak_concepts:
            recommendations.append(
                f"Повторите слабые концепты: {', '.join([c['name'] for c in weak_concepts[:3]])}"
            )
        if unexplored:
            recommendations.append(
                f"Изучите новые темы: {', '.join([c['name'] for c in unexplored[:3]])}"
            )
        
        if not recommendations:
            recommendations.append("Отличная работа! Blind zones не обнаружены.")
        
        return {
            "blind_zones": blind_zones[:10],  # Топ-10
            "total": len(blind_zones),
            "recommendations": recommendations,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate blind zones: {str(exc)}"
        )






