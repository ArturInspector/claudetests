from __future__ import annotations

from app.models import Iteration


def build_feedback_prompt(question: str, answer: str, context: list[str]) -> str:
    context_block = "\n\n".join(context) if context else "Нет дополнительного контекста."
    return (
        "Ты — наставник по обучению. Оцени глубину ответа без оценок в баллах.\n"
        "Верни кратко:\n"
        "- Сильные стороны\n"
        "- Недостающие детали\n"
        "- Следующий шаг (одним предложением)\n\n"
        f"Вопрос: {question}\n"
        f"Ответ: {answer}\n\n"
        f"Контекст из прошлых ответов:\n{context_block}"
    )


def build_session_summary_prompt(topic: str, iterations: list[Iteration]) -> str:
    bullets = []
    for it in iterations:
        bullets.append(
            f"- Итерация {it.number}: вопрос='{it.question[:120]}', вывод='{(it.feedback or '')[:160]}'"
        )
    iterations_text = "\n".join(bullets) if bullets else "Нет итераций."
    return (
        "Сделай краткий отчет о прогрессе ученика по теме. "
        "Укажи текущие пробелы и конкретные рекомендации.\n\n"
        f"Тема: {topic}\n"
        f"Хронология:\n{iterations_text}"
    )

