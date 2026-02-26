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


def build_socratic_moves_prompt(
    question: str,
    answer: str,
    context: list[str] | None = None,
    goal: str | None = None,
    understanding: float | None = None,
    confidence: float | None = None,
    gaps: list[dict] | None = None,
    misconceptions: list[str] | None = None,
    dialogue_history: list[dict] | None = None,
    prior_gaps: list[dict] | None = None,
) -> str:
    """
    Просим LLM сгенерировать ходы и выбрать один лучший вопрос.
    Учитывает историю диалога и ранее выявленные пробелы для адаптивного следования.
    Возвращаемое JSON должно включать selected_question и selection_rationale.
    
    ВАЖНЫЕ ТРЕБОВАНИЯ К ВОПРОСАМ:
    - Ожидаемая глубина ответа: 2-3 параграфа с конкретными примерами, числами, реальными системами (AWS/GCP/etc)
    - Обязательный анализ trade-offs: всегда объяснять pros/cons, когда использовать X vs Y
    - Антипаттерн: избегать абстрактных вопросов типа "Опиши X"
    - Правильный подход: "Опиши X: какие последствия для системы при failure? Приведи пример инцидента."
    """
    ctx = "\n".join(context or []) or "Нет предыдущего контекста."
    target = goal or "Углубить понимание и выявить пробелы."
    u = understanding if understanding is not None else "н/д"
    c = confidence if confidence is not None else "н/д"

    dialogue_block = ""
    if dialogue_history:
        lines = [
            f"  [{msg.get('role', '?')}] {msg.get('content', '')}"
            for msg in dialogue_history[-10:]
        ]
        dialogue_block = (
            "ИСТОРИЯ ДИАЛОГА В ЭТОЙ СЕССИИ (уже обсуждено — не повторяй, опирайся на прогресс):\n"
            + "\n".join(lines)
            + "\n\n"
        )

    prior_gaps_block = ""
    if prior_gaps:
        prior_lines = [
            f"  • {g.get('label', '')} (важность: {g.get('importance', 'н/д')})"
            for g in prior_gaps[-15:]
        ]
        prior_gaps_block = (
            "РАНЕЕ ВЫЯВЛЕННЫЕ ПРОБЕЛЫ (учитывай при выборе следующего вопроса; можно ссылаться: «раньше не было X, теперь...»):\n"
            + "\n".join(prior_lines)
            + "\n\n"
        )

    # Форматирование пробелов с новой структурой
    if gaps:
        gaps_lines = []
        for gap in gaps:
            if isinstance(gap, dict):
                importance = gap.get('importance', 'важно')
                importance_mark = '🔴' if importance == 'критично' else '🟡' if importance == 'важно' else '⚪'
                gaps_lines.append(
                    f"  {importance_mark} {gap.get('label', 'Неизвестный пробел')}\n"
                    f"     Подсказка: {gap.get('hint', 'нет подсказки')}\n"
                    f"     Важность: {importance}\n"
                    f"     Почему важно: {gap.get('why', 'не указано')}"
                )
            else:
                gaps_lines.append(f"  • {gap}")
        gaps_text = "\n".join(gaps_lines)
    else:
        gaps_text = "Нет явных пробелов."
    
    misconceptions_text = "- " + "\n- ".join(misconceptions or []) if misconceptions else "Нет явных заблуждений."

    return (
        "Ты — наставник, использующий сократический метод. "
        "Не давай готовых ответов, но подводи ученика. Задай один лучший вопрос, который продвинет понимание. Помогай подводящими терминами."
        "Учитывай историю диалога: следующий вопрос должен следовать из ответа и ранее выявленных пробелов.\n\n"
        f"{dialogue_block}"
        f"{prior_gaps_block}"
        f"Текущий вопрос: {question}\n"
        f"Ответ ученика: {answer}\n"
        f"Контекст из RAG (похожие ответы):\n{ctx}\n\n"
        f"Цель: {target}\n\n"
        f"Метрики: understanding={u}, confidence={c}\n\n"
        f"Пробелы (gaps):\n{gaps_text}\n\n"
        f"Заблуждения (misconceptions):\n{misconceptions_text}\n\n"
        "КРИТЕРИИ КАЧЕСТВА ВОПРОСОВ:\n"
        "1. Ожидаемая глубина ответа: 2-3 параграфа с конкретными примерами\n"
        "   - Должны быть упомянуты реальные системы (AWS, GCP, Cassandra, DynamoDB и т.д.)\n"
        "   - Должны быть конкретные числа/метрики (latency, throughput, availability %)\n\n"
        "2. Обязательный анализ trade-offs:\n"
        "   - Всегда объяснять pros AND cons\n"
        "   - Когда использовать X vs Y\n"
        "   - Какие последствия выбора для системы\n\n"
        "3. АНТИПАТТЕРН — избегать абстрактные вопросы:\n"
        "   ❌ Плохо: 'Опиши что такое partition'\n"
        "   ✅ Хорошо: 'Опиши partition: что происходит с distributed system при network split? "
        "Приведи пример реального инцидента (AWS, GitHub и т.д.)'\n\n"
        "4. Конкретизация через сценарии:\n"
        "   - Всегда добавлять 'что будет если...'\n"
        "   - Просить сравнить на примере конкретной системы\n"
        "   - Требовать trade-off анализ: 'А если выбрать CP для e-commerce, что теряем?'\n\n"
        "Сформулируй 3-5 сократических ходов (probe/challenge/extend/simplify/celebrate). "
        "Затем выбери один ЛУЧШИЙ вопрос и верни его отдельно. Ответ только JSON:\n"
        "{\n"
        '  "moves": [\n'
        '    {"type": "probe", "text": "...", "rationale": "...", "difficulty": "beginner|intermediate|advanced"},\n'
        '    {"type": "challenge", "text": "...", "rationale": "...", "difficulty": "..."},\n'
        '    {"type": "extend", "text": "...", "rationale": "...", "difficulty": "..."}\n'
        "  ],\n"
        '  "next_step": "краткая рекомендация",\n'
        '  "selected_question": "один лучший вопрос",\n'
        '  "selection_rationale": "почему выбран именно он"\n'
        "}\n"
        "Только JSON."
    )

