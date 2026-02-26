"""Hybrid analysis engine: structured criteria + LLM nuances."""
from __future__ import annotations

import json
import re
from typing import TypedDict, TYPE_CHECKING

from app.services import prompts
from app.services.llm.base import LLMClient
from app.services.rag import RAGService

if TYPE_CHECKING:
    from app.services.graph import GraphBuilderService


class StructuredCriteria(TypedDict):
    """Результаты структурированной проверки ответа."""
    mentions_key_terms: bool
    has_examples: bool
    explains_tradeoffs: bool
    uses_technical_depth: bool
    word_count: int


class AnalysisResult(TypedDict):
    """Финальный результат анализа."""
    understanding_score: float
    structured_criteria: StructuredCriteria
    strengths: list[str]
    weaknesses: list[str]
    mentioned_concepts: list[str]
    blind_zones: list[str]


def check_key_terms(answer: str, required_terms: list[str]) -> bool:
    """Проверяет наличие ключевых терминов в ответе."""
    answer_lower = answer.lower()
    found_count = sum(1 for term in required_terms if term.lower() in answer_lower)
    # Требуется минимум 50% терминов
    return found_count >= len(required_terms) * 0.5


def extract_examples(answer: str) -> list[str]:
    """Извлекает примеры из ответа (например, "например", "for example", code blocks)."""
    examples = []
    
    # Паттерны для примеров
    example_patterns = [
        r'(?:например|example|instance)[\s:]+([^.!?]+)',
        r'```[\w]*\n(.*?)```',
    ]
    
    for pattern in example_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE | re.DOTALL)
        examples.extend(matches)
    
    return [ex.strip() for ex in examples if ex.strip()]


def check_tradeoff_structure(answer: str) -> bool:
    """Проверяет наличие trade-off анализа (плюсы/минусы, но/однако)."""
    tradeoff_indicators = [
        'но', 'однако', 'however', 'but',
        'плюс', 'минус', 'pros', 'cons',
        'advantage', 'disadvantage', 'преимущество', 'недостаток',
        'с другой стороны', 'on the other hand'
    ]
    
    answer_lower = answer.lower()
    return any(indicator in answer_lower for indicator in tradeoff_indicators)


def assess_technical_depth(answer: str) -> bool:
    """Оценивает техническую глубину (специфические термины, метрики, числа)."""
    # Проверка на наличие чисел/метрик
    has_metrics = bool(re.search(r'\d+\s*(?:ms|mb|gb|kb|%|секунд)', answer, re.IGNORECASE))
    
    # Проверка на технические термины (минимальный набор)
    technical_indicators = [
        'algorithm', 'алгоритм', 'complexity', 'сложность',
        'performance', 'производительность', 'latency', 'задержка',
        'throughput', 'пропускная', 'consistency', 'консистентность'
    ]
    
    answer_lower = answer.lower()
    has_technical_terms = any(term in answer_lower for term in technical_indicators)
    
    return has_metrics or has_technical_terms


def extract_mentioned_concepts(answer: str) -> list[str]:
    """Извлекает упомянутые концепции из ответа (capitalized words, технические термины)."""
    # Паттерн для технических терминов и названий (capitalized или в кавычках)
    concept_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b|"([^"]+)"'
    matches = re.findall(concept_pattern, answer)
    
    concepts = []
    for match in matches:
        concept = match[0] or match[1]
        if concept and len(concept) > 3:  # Фильтруем короткие слова
            concepts.append(concept.strip())
    
    return list(set(concepts))[:10]  # Максимум 10 уникальных


def analyze_answer_structured(
    answer: str,
    question: str,
    required_terms: list[str] | None = None
) -> StructuredCriteria:
    """
    Выполняет структурированную проверку ответа по критериям.
    
    Args:
        answer: Текст ответа пользователя
        question: Текст вопроса
        required_terms: Список ключевых терминов для проверки
    
    Returns:
        StructuredCriteria с результатами проверки
    """
    required_terms = required_terms or []
    
    return StructuredCriteria(
        mentions_key_terms=check_key_terms(answer, required_terms),
        has_examples=len(extract_examples(answer)) > 0,
        explains_tradeoffs=check_tradeoff_structure(answer),
        uses_technical_depth=assess_technical_depth(answer),
        word_count=len(answer.split())
    )


def calculate_base_score(criteria: StructuredCriteria) -> float:
    """
    Вычисляет базовый score на основе структурированных критериев.
    
    Веса:
    - key_terms: 0.3
    - examples: 0.2
    - tradeoffs: 0.25
    - technical_depth: 0.15
    - word_count: 0.1 (бонус за достаточный объём)
    """
    score = 0.0
    
    if criteria['mentions_key_terms']:
        score += 0.3
    
    if criteria['has_examples']:
        score += 0.2
    
    if criteria['explains_tradeoffs']:
        score += 0.25
    
    if criteria['uses_technical_depth']:
        score += 0.15
    
    # Бонус за достаточный объём (50+ слов)
    if criteria['word_count'] >= 50:
        score += 0.1
    
    return min(score, 1.0)


def build_llm_analysis_prompt(
    question: str,
    answer: str,
    criteria: StructuredCriteria,
    context: list[str]
) -> str:
    """Строит промпт для LLM анализа нюансов ответа."""
    context_text = "\n".join(context) if context else "Нет контекста из прошлых ответов."
    
    return f"""Проанализируй ответ студента на вопрос. Структурные критерии уже проверены.
Твоя задача — оценить НЮАНСЫ: глубину понимания, точность формулировок, связность.

Вопрос: {question}

Ответ студента: {answer}

Структурные критерии (уже проверено):
- Ключевые термины: {'✓' if criteria['mentions_key_terms'] else '✗'}
- Примеры: {'✓' if criteria['has_examples'] else '✗'}
- Trade-offs: {'✓' if criteria['explains_tradeoffs'] else '✗'}
- Техническая глубина: {'✓' if criteria['uses_technical_depth'] else '✗'}
- Объём: {criteria['word_count']} слов

Контекст из прошлых ответов:
{context_text}

Верни JSON:
{{
  "nuance_score": 0.0-1.0,
  "strengths": ["сильная сторона 1", "сильная сторона 2"],
  "weaknesses": ["слабость 1", "слабость 2"],
  "mentioned_concepts": ["концепт 1", "концепт 2"],
  "missing_connections": ["что упущено 1", "что упущено 2"],
  "misconceptions": [
    {{"label": "краткое описание заблуждения", "correction": "корректная формулировка"}}
  ]
}}

misconceptions — только если в ответе есть фактические ошибки или типичные заблуждения по теме (массив может быть пустым). Только JSON, без дополнительного текста."""


async def analyze_with_llm(
    llm: LLMClient,
    rag: RAGService,
    user_id: int,
    question: str,
    answer: str,
    criteria: StructuredCriteria
) -> dict:
    """
    Использует LLM для анализа нюансов ответа.
    
    Args:
        llm: LLM клиент
        rag: RAG сервис для контекста
        user_id: ID пользователя
        question: Текст вопроса
        answer: Текст ответа
        criteria: Результаты структурной проверки
    
    Returns:
        Словарь с результатами LLM анализа
    """
    try:
        context = await rag.similar_context(user_id=user_id, text=question, limit=3)
    except Exception:
        context = []

    # Строим промпт
    prompt = build_llm_analysis_prompt(question, answer, criteria, context)
    
    # Запрашиваем LLM
    response = await llm.generate(prompt)
    
    # Парсим JSON ответ
    try:
        # Извлекаем JSON из ответа (может быть обёрнут в markdown)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            result = json.loads(response)
        
        misconceptions = result.get('misconceptions') or []
        if not isinstance(misconceptions, list):
            misconceptions = []
        return {
            'nuance_score': result.get('nuance_score', 0.5),
            'strengths': result.get('strengths', []),
            'weaknesses': result.get('weaknesses', []),
            'mentioned_concepts': result.get('mentioned_concepts', []),
            'missing_connections': result.get('missing_connections', []),
            'misconceptions': [
                m if isinstance(m, dict) else {'label': str(m), 'correction': ''}
                for m in misconceptions
            ],
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            'nuance_score': 0.5,
            'strengths': ['Ответ получен'],
            'weaknesses': ['Не удалось детально проанализировать'],
            'mentioned_concepts': extract_mentioned_concepts(answer),
            'missing_connections': [],
            'misconceptions': [],
        }


async def analyze_answer_hybrid(
    llm: LLMClient,
    rag: RAGService,
    user_id: int,
    question: str,
    answer: str,
    required_terms: list[str] | None = None
) -> AnalysisResult:
    """
    Гибридный анализ: структурные критерии + LLM нюансы.
    
    Args:
        llm: LLM клиент
        rag: RAG сервис
        user_id: ID пользователя
        question: Текст вопроса
        answer: Текст ответа
        required_terms: Ключевые термины для проверки
    
    Returns:
        AnalysisResult с полным анализом
    """
    # Шаг 1: Структурная проверка (быстро, детерминированно)
    criteria = analyze_answer_structured(answer, question, required_terms)
    base_score = calculate_base_score(criteria)
    
    # Шаг 2: LLM анализ нюансов (медленно, но глубоко)
    llm_result = await analyze_with_llm(llm, rag, user_id, question, answer, criteria)
    
    # Шаг 3: Комбинируем результаты (70% структура, 30% LLM)
    final_score = base_score * 0.7 + llm_result['nuance_score'] * 0.3
    
    return AnalysisResult(
        understanding_score=final_score,
        structured_criteria=criteria,
        strengths=llm_result['strengths'],
        weaknesses=llm_result['weaknesses'],
        mentioned_concepts=llm_result['mentioned_concepts'],
        blind_zones=llm_result['missing_connections']
    )


def calculate_graph_blind_zones(
    user_graph: dict,
    mentioned_concepts: list[str]
) -> list[str]:
    """
    Вычисляет blind zones на основе knowledge graph.
    
    Blind zones — это:
    1. Unexplored branches (концепты связанные с известными, но не изученные)
    2. Weak connections (mastery_level < 0.5)
    3. Forgotten concepts (давно не повторялись)
    
    Args:
        user_graph: Граф знаний пользователя из Neo4j
        mentioned_concepts: Концепты упомянутые в текущем ответе
    
    Returns:
        Список blind zones с описаниями
    """
    blind_zones = []
    
    concepts = user_graph.get('concepts', [])
    knowledge = user_graph.get('knowledge', [])
    
    if not concepts:
        return ['Граф знаний пуст — начните с основ темы']
    
    # Строим map концептов по имени для быстрого доступа
    concept_map = {c.get('name', ''): c for c in concepts}
    
    # Строим map mastery levels
    mastery_map = {}
    for k in knowledge:
        # k — это KNOWS relationship
        concept_name = k.get('end_node_name')  # Предполагаем что Neo4j вернёт имя
        if concept_name:
            mastery_map[concept_name] = k.get('mastery_level', 0.0)
    
    # 1. Находим слабые концепты (mastery < 0.5)
    weak_concepts = [
        name for name, level in mastery_map.items()
        if level < 0.5
    ]
    
    if weak_concepts:
        blind_zones.append(
            f"Слабое понимание: {', '.join(weak_concepts[:3])}"
        )
    
    # 2. Находим неупомянутые концепты из графа
    mentioned_set = set(c.lower() for c in mentioned_concepts)
    known_concepts = set(concept_map.keys())
    
    not_mentioned = [
        name for name in known_concepts
        if name.lower() not in mentioned_set
    ]
    
    if not_mentioned and len(not_mentioned) > 2:
        blind_zones.append(
            f"Не упомянуты связанные концепты: {', '.join(not_mentioned[:3])}"
        )
    
    # 3. Проверяем есть ли unexplored branches
    # (концепты с низким times_reviewed)
    unexplored = [
        c.get('name') for c in concepts
        if c.get('times_reviewed', 0) <= 1
    ]
    
    if unexplored:
        blind_zones.append(
            f"Мало практики: {', '.join(unexplored[:2])}"
        )
    
    return blind_zones if blind_zones else ['Blind zones не обнаружены']


async def analyze_with_graph(
    llm: LLMClient,
    rag: RAGService,
    graph: 'GraphBuilderService',
    user_id: str,
    question: str,
    answer: str,
    topic: str,
    session_id: str,
    required_terms: list[str] | None = None
) -> AnalysisResult:
    """
    Полный анализ с интеграцией knowledge graph.
    
    Workflow:
    1. Структурная проверка
    2. LLM анализ нюансов
    3. Извлечение концептов и обновление графа
    4. Вычисление graph-based blind zones
    
    Args:
        llm: LLM клиент
        rag: RAG сервис
        graph: Graph builder сервис
        user_id: ID пользователя (строка для Neo4j)
        question: Текст вопроса
        answer: Текст ответа
        topic: Тема сессии
        session_id: ID сессии (строка)
        required_terms: Ключевые термины
    
    Returns:
        AnalysisResult с полным анализом включая graph blind zones
    """
    # Шаг 1-2: Базовый гибридный анализ
    criteria = analyze_answer_structured(answer, question, required_terms)
    base_score = calculate_base_score(criteria)
    
    llm_result = await analyze_with_llm(
        llm, rag, int(user_id) if user_id.isdigit() else 0, question, answer, criteria
    )
    
    # Шаг 3–4: Граф (best-effort, fallback при ошибке)
    all_concepts = list(llm_result['mentioned_concepts'])
    combined_blind_zones = list(llm_result['missing_connections'])
    try:
        extracted_concepts = await graph.extract_concepts(
            user_id=user_id,
            question=question,
            answer=answer,
            topic=topic,
            session_id=session_id,
        )
        all_concepts = list(set(
            all_concepts + [c.get('name', '') for c in extracted_concepts if c.get('name')]
        ))
        user_graph = await graph.get_user_graph(user_id=user_id, depth=2)
        graph_blind_zones = calculate_graph_blind_zones(user_graph, all_concepts)
        combined_blind_zones = list(set(combined_blind_zones + graph_blind_zones))
    except Exception:
        pass  # Анализ без графа: только LLM blind zones

    final_score = base_score * 0.7 + llm_result['nuance_score'] * 0.3
    return AnalysisResult(
        understanding_score=final_score,
        structured_criteria=criteria,
        strengths=llm_result['strengths'],
        weaknesses=llm_result['weaknesses'],
        mentioned_concepts=all_concepts,
        blind_zones=combined_blind_zones,
    )


async def analyze_answer_socratic(
    llm: LLMClient,
    rag: RAGService,
    graph: "GraphBuilderService",
    user_id: int,
    question: str,
    answer: str,
    topic: str,
    session_id: str,
    required_terms: list[str] | None = None,
    mode: str = "practice",
    dialogue_history: list[dict] | None = None,
    prior_gaps: list[dict] | None = None,
):
    """Гибридный сократический анализ с учётом контекста диалога и ранее выявленных пробелов."""
    required_terms = required_terms or []
    dialogue_history = dialogue_history or []
    prior_gaps = prior_gaps or []

    # 1) Structured
    criteria = analyze_answer_structured(answer, question, required_terms)
    base_score = calculate_base_score(criteria)
    gaps_list: list[dict] = []
    if not criteria["mentions_key_terms"]:
        gaps_list.append({
            "label": "Не упомянуты ключевые термины",
            "hint": "Перечисли основные понятия темы с кратким определением каждого (1-2 предложения)",
            "importance": "критично",
            "why": "Без базовой терминологии невозможно обсуждать детали и trade-offs"
        })
    if not criteria["explains_tradeoffs"]:
        gaps_list.append({
            "label": "Нет анализа trade-off",
            "hint": "Опиши pros AND cons выбора, приведи сценарий когда X лучше Y (2-3 предложения)",
            "importance": "критично",
            "why": "В реальных системах всё решается через trade-offs: нет серебряной пули"
        })
    if not criteria["has_examples"]:
        gaps_list.append({
            "label": "Нет конкретных примеров",
            "hint": "Приведи пример из реального проекта или известной системы (AWS, GitHub, Netflix и т.д.)",
            "importance": "важно",
            "why": "Примеры показывают применение концепции в production, а не просто теорию"
        })
    if not criteria["uses_technical_depth"]:
        gaps_list.append({
            "label": "Низкая техническая глубина",
            "hint": "Добавь конкретные метрики (latency ms, throughput req/s, availability %) или алгоритмы",
            "importance": "важно",
            "why": "Глубина понимания видна через детали: числа, алгоритмы, ограничения систем"
        })

    # 2) LLM nuance
    llm_result = await analyze_with_llm(llm, rag, user_id, question, answer, criteria)
    nuance = llm_result.get("nuance_score", 0.5)
    understanding = round(base_score * 0.7 + nuance * 0.3, 3)
    confidence = round(0.4 + nuance * 0.6, 3)

    # 3) Socratic moves — RAG context with fallback
    try:
        context = await rag.similar_context(user_id=user_id, text=question, limit=3)
    except Exception:
        context = []

    # Misconceptions from LLM (topic-agnostic)
    misconceptions_from_llm = llm_result.get("misconceptions") or []
    misconceptions_labels = [m.get("label", "") for m in misconceptions_from_llm if isinstance(m, dict)]
    
    moves_payload = prompts.build_socratic_moves_prompt(
        question=question,
        answer=answer,
        context=context,
        goal=None,
        understanding=understanding,
        confidence=confidence,
        gaps=gaps_list,
        misconceptions=misconceptions_labels,
        dialogue_history=dialogue_history,
        prior_gaps=prior_gaps,
    )
    try:
        moves_resp = await llm.generate(moves_payload)
        json_match = re.search(r"\{.*\}", moves_resp, re.DOTALL)
        moves_data = json.loads(json_match.group(0) if json_match else moves_resp)
        moves = moves_data.get("moves", [])
        next_step = moves_data.get("next_step")
        selected_question = moves_data.get("selected_question")
        selection_rationale = moves_data.get("selection_rationale")
    except Exception:
        moves = [
            {"type": "probe", "text": "Уточни свой ответ: приведи пример или разверни мысль."},
            {"type": "extend", "text": "Что будет, если применить это в реальной системе? Опиши trade-offs."},
        ]
        next_step = "Уточни ответ или приведи пример — тогда задам следующий вопрос."
        selected_question = moves[0]["text"] if moves else "Уточни свой ответ."
        selection_rationale = "LLM недоступен, выбран базовый наводящий вопрос."

    # 4) Misconceptions from LLM + difficulty
    misconceptions = misconceptions_from_llm
    next_difficulty = "advanced" if understanding > 0.7 else "intermediate" if understanding > 0.4 else "beginner"

    # 4.1) Локальный выбор вопроса, если LLM не вернул selected_question
    def _pick_fallback_question() -> tuple[str, str]:
        if understanding < 0.5:
            for mv in moves:
                if mv.get("type") == "simplify":
                    return mv.get("text", ""), "Понимание <50%, упрощаем."
            for mv in moves:
                if mv.get("type") == "probe":
                    return mv.get("text", ""), "Понимание <50%, уточняем через probe."
        if misconceptions:
            for mv in moves:
                if mv.get("type") == "challenge":
                    return mv.get("text", ""), "Есть заблуждения, задаём challenge."
        if gaps_list:
            for mv in moves:
                if mv.get("type") == "probe":
                    return mv.get("text", ""), "Есть пробелы, уточняем через probe."
        if moves:
            return moves[0].get("text", ""), "Берём первый сгенерированный ход."
        return "Уточни ключевой trade-off для своей системы.", "Нет ходов, fallback."

    if not selected_question:
        selected_question, selection_rationale = _pick_fallback_question()

    # 5) Graph hints (best-effort)
    graph_hints: list[dict] = []
    blind_zones: list[str] | None = None
    try:
        user_graph = await graph.get_user_graph(user_id=str(user_id), depth=2)
        graph_blind = calculate_graph_blind_zones(user_graph, llm_result.get("mentioned_concepts", []))
        blind_zones = graph_blind
        if graph_blind:
            for zone in graph_blind[:3]:
                graph_hints.append({"concept": zone, "status": "weak"})
    except Exception:
        blind_zones = None

    # Конвертируем gaps для фронтенда (добавляем done=false для всех)
    gaps_for_frontend = [
        {
            "label": gap["label"],
            "hint": gap["hint"],
            "importance": gap["importance"],
            "why": gap["why"],
            "done": False
        }
        for gap in gaps_list
    ]

    return {
        "analysis": {
          "understanding": understanding,
          "confidence": confidence,
          "misconceptions": misconceptions,
          "nextDifficulty": next_difficulty,
          "gaps": gaps_for_frontend,
        },
        "socratic": {
            "moves": moves,
            "next_step": next_step,
            "selected_question": selected_question,
            "selection_rationale": selection_rationale,
        },
        "graph": {"hints": graph_hints} if graph_hints else None,
        "blind_zones": blind_zones,
    }

