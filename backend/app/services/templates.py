"""
Session Templates System.

Предоставляет готовые шаблоны для разных режимов обучения:
- Interview Prep: быстрые вопросы для подготовки к интервью
- System Design: архитектурные вопросы с trade-offs
- Deep Dive: глубокое изучение с детальным разбором
"""
from __future__ import annotations

from enum import Enum
from typing import TypedDict


class TemplateType(str, Enum):
    """Типы доступных шаблонов."""
    INTERVIEW_PREP = "interview_prep"
    SYSTEM_DESIGN = "system_design"
    DEEP_DIVE = "deep_dive"


class QuestionConfig(TypedDict):
    """Конфигурация генерации вопросов для шаблона."""
    max_questions: int
    time_per_question_minutes: int
    difficulty_progression: bool
    focus_on_weak_areas: bool
    include_followups: bool


class TemplateMetadata(TypedDict):
    """Метаданные шаблона."""
    name: str
    description: str
    recommended_duration_minutes: int
    target_audience: str
    question_config: QuestionConfig


class SessionTemplate:
    """
    Базовый класс для session templates.
    
    Каждый шаблон определяет:
    - Стратегию генерации вопросов
    - Критерии оценки ответов
    - Формат фидбека
    """
    
    def __init__(self, metadata: TemplateMetadata):
        self.metadata = metadata
    
    def get_system_prompt(self, topic: str, user_context: dict | None = None) -> str:
        """
        Генерирует system prompt для LLM на основе шаблона.
        
        Args:
            topic: Тема сессии
            user_context: Контекст пользователя (prior knowledge, weak areas)
        
        Returns:
            System prompt для LLM
        """
        raise NotImplementedError("Subclasses must implement get_system_prompt")
    
    def get_question_prompt(
        self,
        topic: str,
        iteration_number: int,
        previous_answers: list[str] | None = None,
        weak_areas: list[str] | None = None
    ) -> str:
        """
        Генерирует prompt для создания следующего вопроса.
        
        Args:
            topic: Тема сессии
            iteration_number: Номер текущей итерации
            previous_answers: Предыдущие ответы пользователя
            weak_areas: Слабые области из графа знаний
        
        Returns:
            Prompt для генерации вопроса
        """
        raise NotImplementedError("Subclasses must implement get_question_prompt")
    
    def get_feedback_criteria(self) -> list[str]:
        """
        Возвращает критерии для оценки ответа.
        
        Returns:
            Список критериев специфичных для шаблона
        """
        raise NotImplementedError("Subclasses must implement get_feedback_criteria")


def get_template(template_type: TemplateType) -> SessionTemplate:
    """
    Factory function для получения шаблона по типу.
    
    Args:
        template_type: Тип шаблона
    
    Returns:
        Экземпляр SessionTemplate
    
    Raises:
        ValueError: Если template_type неизвестен
    """
    templates = {
        TemplateType.INTERVIEW_PREP: _create_interview_prep_template,
        TemplateType.SYSTEM_DESIGN: _create_system_design_template,
        TemplateType.DEEP_DIVE: _create_deep_dive_template,
    }
    
    factory = templates.get(template_type)
    if not factory:
        raise ValueError(f"Unknown template type: {template_type}")
    
    return factory()


def _create_interview_prep_template() -> SessionTemplate:
    """Placeholder для Interview Prep template."""
    # Будет реализовано в следующем коммите
    raise NotImplementedError("Interview Prep template not yet implemented")


def _create_system_design_template() -> SessionTemplate:
    """Placeholder для System Design template."""
    # Будет реализовано в следующем коммите
    raise NotImplementedError("System Design template not yet implemented")


def _create_deep_dive_template() -> SessionTemplate:
    """Placeholder для Deep Dive template."""
    # Будет реализовано в следующем коммите
    raise NotImplementedError("Deep Dive template not yet implemented")

