# Changelog - Deep Learning Platform

## v2.0.0 - Deep Learning Features (2025-01-13)

### 🚀 Major Features

**Многоуровневая система обучения:**
- Progressive Disclosure (L1→L2→L3→L4)
- Каждый концепт разбит на уровни понимания
- Автоматическое определение сложности по уровню

**Spaced Repetition:**
- Алгоритм повторений (упрощенный SM-2)
- Автоматический расчет следующей даты повторения
- Confidence-based интервалы (1-5 звездочек)
- Dedicated /review страница

**Расширенная аналитика:**
- Time tracking для вопросов
- Confidence level после каждого ответа
- Weak spots detection с рекомендациями
- Knowledge Map по уровням

**Ресурсы и заметки:**
- Автоматическое извлечение ресурсов из .md файлов
- Автосохранение личных заметок
- Связи между концептами (related concepts)

### 🎨 UI/UX Improvements

**practice.html:**
- Level indicators (L1-L4) с цветовой кодировкой
- Tags display для быстрой навигации
- Таймеры (общий + для вопроса)
- Confidence rating (5 уровней)
- Sidebar с related concepts
- Секция ресурсов (видео, статьи, код)
- Notes с автосохранением

**review.html (новая):**
- Dashboard с статистикой повторений
- Queue вопросов на сегодня
- Emoji-based confidence rating
- Прогресс бар
- Completion screen

**stats.html:**
- Knowledge Map (прогресс по L1-L4)
- Retention section (интеграция с spaced repetition)
- Weak Spots с рекомендациями и советами
- Улучшенная визуализация активности

### 🔧 Backend Changes

**Database:**
- Новые таблицы: `resources`, `user_notes`, `concept_links`
- Расширен `questions`: `level`, `parent_concept_id`, `tags`, `estimated_time`
- Расширен `user_answers`: `time_spent`, `showed_answer`, `confidence_level`, `next_review_date`, `review_count`

**API Endpoints (новые):**
```
GET  /review - Review page
GET  /api/review/queue - Вопросы на повторение
POST /api/review/update - Обновить статус повторения
GET  /api/review/stats - Статистика повторений
POST /api/resources - Создать ресурс
GET  /api/resources/{question_id} - Получить ресурсы
POST /api/notes - Сохранить заметку
GET  /api/notes/{question_id} - Получить заметку
DELETE /api/notes/{question_id} - Удалить заметку
GET  /api/questions/{question_id}/related - Связанные вопросы
GET  /api/questions/level/{topic_id}/{level} - Вопросы по уровню
GET  /api/questions/{question_id}/children - Подвопросы (progressive)
```

**Parser:**
- Поддержка многоуровневых концептов
- Парсинг Tags, Estimated Time
- Извлечение Resources из .md
- Извлечение Related Concepts
- Обратная совместимость

### 📝 Примеры использования

**Старый формат (все еще работает):**
```markdown
# Topic: Solidity

## Question: What is reentrancy?
**Difficulty**: Medium
**Type**: Text

Question text...

**Answer**:
Answer text...
```

**Новый формат (многоуровневый):**
```markdown
# Topic: Solidity Advanced

## Concept: Reentrancy Attacks
**Tags**: security, vulnerabilities, CEI-pattern
**Estimated Time**: 20 minutes

### Level 1: What is reentrancy?
Question...
**Answer**: Answer...

### Level 2: How does CEI pattern help?
Question...
**Answer**: Answer...

### Level 3: Cross-contract reentrancy
Question...
**Answer**: Answer...

**Resources**:
- [Video] https://youtube.com/... - Title
- [Article] https://... - Title

**Related Concepts**: CEI Pattern, State Mutations
```

### 🔄 Migration

База данных автоматически обновится при первом запуске. Старые вопросы получат `level=1` по умолчанию.

---

## v1.0.0 - Initial Release

- Базовая система вопросов/ответов
- Импорт из .md файлов
- Статистика по темам
- Сессии практики
- Summary для копирования

