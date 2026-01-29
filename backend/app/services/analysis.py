"""Hybrid analysis engine: structured criteria + LLM nuances."""
from __future__ import annotations

import re
from typing import TypedDict


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

