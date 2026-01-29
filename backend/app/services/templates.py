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


class InterviewPrepTemplate(SessionTemplate):
    """
    Interview Prep режим: быстрые вопросы для подготовки к интервью.
    
    Особенности:
    - Короткие вопросы (2-3 минуты на ответ)
    - Фокус на weak areas из графа
    - Прогрессия сложности
    - Практические примеры обязательны
    """
    
    def get_system_prompt(self, topic: str, user_context: dict | None = None) -> str:
        weak_areas = user_context.get('weak_areas', []) if user_context else []
        weak_areas_text = ', '.join(weak_areas) if weak_areas else 'не определены'
        
        return f"""Ты — интервьюер для технического собеседования по теме: {topic}.

Твоя задача: задавать короткие, конкретные вопросы для проверки понимания.

Правила:
1. Вопросы должны быть короткими (1-2 предложения)
2. Требуй конкретных примеров и чисел
3. Фокусируйся на практическом применении
4. Если студент ошибается — задай уточняющий вопрос

Слабые области студента: {weak_areas_text}

Начинай с базовых вопросов, постепенно усложняй."""
    
    def get_question_prompt(
        self,
        topic: str,
        iteration_number: int,
        previous_answers: list[str] | None = None,
        weak_areas: list[str] | None = None
    ) -> str:
        context = ""
        if previous_answers and len(previous_answers) > 0:
            last_answer = previous_answers[-1][:200]  # Первые 200 символов
            context = f"\nПредыдущий ответ студента: {last_answer}..."
        
        weak_focus = ""
        if weak_areas:
            weak_focus = f"\nСлабые области: {', '.join(weak_areas[:2])}"
        
        difficulty = "базовый" if iteration_number <= 2 else "средний" if iteration_number <= 4 else "продвинутый"
        
        return f"""Сгенерируй следующий вопрос для интервью по теме: {topic}

Итерация: {iteration_number}
Уровень сложности: {difficulty}{context}{weak_focus}

Требования:
- Вопрос должен быть коротким и конкретным
- Требуй практических примеров
- Если предыдущий ответ слабый — задай уточняющий вопрос
- Если ответ сильный — переходи к новому аспекту темы

Верни только текст вопроса, без дополнительных пояснений."""
    
    def get_feedback_criteria(self) -> list[str]:
        return [
            "Конкретность ответа (есть ли примеры?)",
            "Практическое понимание (может ли применить?)",
            "Точность терминологии",
            "Скорость ответа (для интервью важна)",
        ]


def _create_interview_prep_template() -> SessionTemplate:
    """Создаёт Interview Prep template."""
    metadata = TemplateMetadata(
        name="Interview Prep",
        description="Быстрая подготовка к техническому интервью",
        recommended_duration_minutes=30,
        target_audience="Кандидаты готовящиеся к собеседованиям",
        question_config=QuestionConfig(
            max_questions=10,
            time_per_question_minutes=3,
            difficulty_progression=True,
            focus_on_weak_areas=True,
            include_followups=True,
        )
    )
    return InterviewPrepTemplate(metadata)


class SystemDesignTemplate(SessionTemplate):
    """
    System Design режим: архитектурные вопросы с trade-offs.
    
    Особенности:
    - Открытые вопросы (5-10 минут на ответ)
    - Обязательный анализ trade-offs
    - Масштабируемость и надёжность
    - Реальные кейсы
    """
    
    def get_system_prompt(self, topic: str, user_context: dict | None = None) -> str:
        return f"""Ты — архитектор системы, проводящий System Design интервью по теме: {topic}.

Твоя задача: задавать открытые архитектурные вопросы.

Правила:
1. Вопросы должны требовать анализа trade-offs
2. Спрашивай про масштабируемость, надёжность, производительность
3. Требуй обоснования архитектурных решений
4. Задавай уточняющие вопросы про edge cases

Формат: "Спроектируй систему для..." или "Как бы ты решил проблему..."

Оценивай не только решение, но и процесс мышления."""
    
    def get_question_prompt(
        self,
        topic: str,
        iteration_number: int,
        previous_answers: list[str] | None = None,
        weak_areas: list[str] | None = None
    ) -> str:
        context = ""
        if previous_answers and len(previous_answers) > 0:
            last_answer = previous_answers[-1][:300]
            context = f"\nПредыдущее решение: {last_answer}..."
        
        return f"""Сгенерируй System Design вопрос по теме: {topic}

Итерация: {iteration_number}{context}

Требования:
- Вопрос должен быть открытым (нет единственно правильного ответа)
- Требуй анализа trade-offs
- Включи constraints (например: "1M пользователей", "99.9% uptime")
- Если предыдущий ответ не рассмотрел trade-offs — задай уточняющий вопрос

Примеры хороших вопросов:
- "Спроектируй URL shortener для 100M запросов в день"
- "Как обеспечить консистентность в распределённой системе?"

Верни только текст вопроса."""
    
    def get_feedback_criteria(self) -> list[str]:
        return [
            "Анализ trade-offs (рассмотрены ли альтернативы?)",
            "Масштабируемость решения",
            "Учёт edge cases",
            "Обоснование выбора технологий",
        ]


class DeepDiveTemplate(SessionTemplate):
    """
    Deep Dive режим: глубокое изучение с детальным разбором.
    
    Особенности:
    - Длинные сессии (60+ минут)
    - Последовательное углубление в тему
    - Связь между концептами
    - Теория + практика
    """
    
    def get_system_prompt(self, topic: str, user_context: dict | None = None) -> str:
        prior_knowledge = user_context.get('prior_knowledge', []) if user_context else []
        knowledge_text = ', '.join(prior_knowledge[:5]) if prior_knowledge else 'отсутствует'
        
        return f"""Ты — наставник для глубокого изучения темы: {topic}.

Твоя задача: провести студента от основ к продвинутым концептам.

Правила:
1. Начинай с фундаментальных концептов
2. Постепенно углубляйся, связывая новое с известным
3. Требуй как теоретического понимания, так и практических примеров
4. Задавай "почему?" и "как это связано с...?"

Известные студенту концепты: {knowledge_text}

Строй вопросы так, чтобы создать цельную картину темы."""
    
    def get_question_prompt(
        self,
        topic: str,
        iteration_number: int,
        previous_answers: list[str] | None = None,
        weak_areas: list[str] | None = None
    ) -> str:
        context = ""
        if previous_answers and len(previous_answers) > 0:
            # Берём больше контекста для deep dive
            recent = previous_answers[-2:] if len(previous_answers) > 1 else previous_answers
            context = "\n".join([f"- {ans[:200]}..." for ans in recent])
            context = f"\nПредыдущие ответы:\n{context}"
        
        phase = "основы" if iteration_number <= 3 else "углубление" if iteration_number <= 6 else "продвинутые концепты"
        
        return f"""Сгенерируй вопрос для Deep Dive сессии по теме: {topic}

Итерация: {iteration_number}
Фаза: {phase}{context}

Требования:
- Вопрос должен углублять понимание темы
- Связывай новый материал с предыдущими ответами
- Требуй объяснения "почему" и "как"
- В фазе "основы" — фундаментальные концепты
- В фазе "углубление" — связи между концептами
- В фазе "продвинутые" — edge cases и оптимизации

Верни только текст вопроса."""
    
    def get_feedback_criteria(self) -> list[str]:
        return [
            "Глубина понимания (не поверхностно ли?)",
            "Связь с другими концептами",
            "Теоретическое обоснование",
            "Практические примеры",
            "Понимание 'почему' а не только 'что'",
        ]


def _create_system_design_template() -> SessionTemplate:
    """Создаёт System Design template."""
    metadata = TemplateMetadata(
        name="System Design",
        description="Архитектурные вопросы с анализом trade-offs",
        recommended_duration_minutes=60,
        target_audience="Инженеры уровня Senior+",
        question_config=QuestionConfig(
            max_questions=5,
            time_per_question_minutes=10,
            difficulty_progression=False,  # Все вопросы сложные
            focus_on_weak_areas=False,  # Фокус на целостной архитектуре
            include_followups=True,
        )
    )
    return SystemDesignTemplate(metadata)


def _create_deep_dive_template() -> SessionTemplate:
    """Создаёт Deep Dive template."""
    metadata = TemplateMetadata(
        name="Deep Dive",
        description="Глубокое последовательное изучение темы",
        recommended_duration_minutes=90,
        target_audience="Все уровни, желающие глубоко понять тему",
        question_config=QuestionConfig(
            max_questions=12,
            time_per_question_minutes=7,
            difficulty_progression=True,
            focus_on_weak_areas=True,
            include_followups=True,
        )
    )
    return DeepDiveTemplate(metadata)

