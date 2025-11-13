# Архитектура: Interview Practice Platform

## Обзор системы

Локальное веб-приложение с минималистичным дизайном для практики технических интервью.

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   FastAPI   │
│  (Backend)  │
└──────┬──────┘
       │ SQLAlchemy
       ▼
┌─────────────┐
│   SQLite    │
│  (Database) │
└─────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - современный async веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **SQLite** - легковесная БД (достаточно для локального использования)
- **Python 3.10+**

### Frontend
- **Vanilla HTML/JS** - без тяжелых фреймворков
- **Tailwind CSS** (via CDN) - быстрая стилизация
- **highlight.js** - подсветка синтаксиса кода
- **Jinja2 Templates** - серверный рендеринг

### Почему такой выбор?
- **Простота** - легко запустить и модифицировать
- **Быстрый старт** - нет сложной настройки
- **Минимальные зависимости** - 5 пакетов в requirements.txt
- **Локальность** - не требует внешних сервисов

## Структура базы данных

### ER-диаграмма

```
┌─────────────┐
│   Topics    │
│─────────────│
│ id (PK)     │
│ name        │
│ description │
│ created_at  │
└──────┬──────┘
       │ 1
       │
       │ N
       ▼
┌─────────────┐
│  Questions  │
│─────────────│
│ id (PK)     │
│ topic_id(FK)│
│ title       │
│ difficulty  │
│ type        │
│ question_   │
│   text      │
│ answer_text │
│ created_at  │
└──────┬──────┘
       │ 1
       │
       │ N
       ▼
┌─────────────┐       ┌──────────┐
│UserAnswers  │ N   1 │ Sessions │
│─────────────│◄──────┤──────────│
│ id (PK)     │       │ id (PK)  │
│ question_id │       │ started_ │
│ session_id  │       │   at     │
│ user_answer │       │ ended_at │
│ answered_at │       │ questions│
└─────────────┘       │   _count │
                      │ duration │
                      │ summary  │
                      └──────────┘
```

### Таблицы

**topics**
- Хранит темы вопросов (Solidity, Python, Web3)
- Связь 1:N с questions

**questions**
- Вопросы с правильными ответами
- `difficulty`: Easy/Medium/Hard
- `type`: Text/Code (определяет тип редактора)

**user_answers**
- История ответов пользователя
- Связана с сессией (опционально)
- Используется для статистики

**sessions**
- Сессии практики с метаданными
- Хранит summary для копирования

## Архитектура backend

### Слои приложения

```
┌──────────────────────────────────────┐
│         API Layer (main.py)          │
│  - Endpoints                         │
│  - Request/Response validation       │
│  - Error handling                    │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│      Business Logic (crud.py)        │
│  - CRUD operations                   │
│  - Statistics calculation            │
│  - Session management                │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│      Data Layer (database.py)        │
│  - SQLAlchemy models                 │
│  - Database connection               │
└──────────────────────────────────────┘
```

### Вспомогательные модули

**parser.py**
- Парсинг .md файлов
- Извлечение темы, вопросов, метаданных
- Regex-based парсинг структуры

## Архитектура frontend

### Страницы

**index.html** - Главная
- Список тем с количеством вопросов
- Форма для импорта .md файлов
- Drag & drop загрузка

**practice.html** - Практика
- Отображение вопроса
- Текстовое поле / code editor
- Кнопки "Показать ответ", "Следующий вопрос"
- Summary при завершении сессии

**stats.html** - Статистика
- Общие метрики (всего вопросов, прогресс)
- Прогресс по темам (progress bars)
- История сессий
- График активности

### JavaScript архитектура

```javascript
// API Layer - централизованный доступ к backend
const API = {
    getTopics(),
    getQuestion(topicId, difficulty, sessionId),
    submitAnswer(questionId, answer, sessionId),
    startSession(),
    endSession(sessionId),
    getStats()
}

// Utils - вспомогательные функции
const Utils = {
    formatDate(),
    formatDuration(),
    parseMarkdown(),
    copyToClipboard()
}
```

## Поток данных

### 1. Импорт вопросов

```
User uploads .md file
        │
        ▼
FastAPI receives file
        │
        ▼
parser.py parses content
        │
        ▼
crud.py creates/updates
        │
        ▼
Database stores questions
        │
        ▼
Response to frontend
```

### 2. Практика

```
User selects topic
        │
        ▼
Session created (API)
        │
        ▼
Random question fetched
        │
        ▼
User writes answer
        │
        ▼
Answer saved to DB
        │
        ▼
Show correct answer
        │
        ▼
Next question or end session
        │
        ▼
Generate summary
```

### 3. Статистика

```
User opens stats page
        │
        ▼
Frontend requests /api/stats
        │
        ▼
crud.py calculates:
  - Total questions
  - Answered questions
  - Progress by topics
  - Daily activity
        │
        ▼
Response with JSON
        │
        ▼
Frontend renders charts
```

## API Design

### RESTful endpoints

```
GET  /                      - Index page
GET  /practice              - Practice page
GET  /stats                 - Stats page

POST /api/import            - Upload .md file
GET  /api/topics            - List all topics
GET  /api/question/{id}     - Get random question
GET  /api/question/{id}/answer - Get question with answer
POST /api/answer            - Submit user answer
POST /api/session/start     - Start practice session
POST /api/session/end       - End session, get summary
GET  /api/stats             - Get statistics
GET  /api/sessions/recent   - Get recent sessions
```

## Безопасность и ограничения

### Текущие ограничения
- **Однопользовательская** - нет аутентификации
- **Локальная** - не предназначена для продакшена
- **SQLite** - не подходит для concurrent writes

### Расширение для multi-user
Если нужно:
1. Добавить **users** таблицу
2. JWT authentication
3. Migrate на PostgreSQL
4. Rate limiting
5. CORS настройки

## Performance соображения

### Оптимизации
- **Eager loading** для questions.topic (избегаем N+1)
- **Индексы** на topic_id, session_id
- **Pagination** для /api/questions (если тысячи вопросов)
- **Cache** для /api/stats (если нужно)

### Масштабируемость
Для большого числа вопросов:
- Добавить ElasticSearch для поиска
- Redis для кэширования
- Background jobs для heavy operations

## Deployment

### Локальный запуск
```bash
pip install -r requirements.txt
cd backend
python main.py
```

### Docker (опционально)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0"]
```

## Мониторинг и логи

Для production можно добавить:
- **Logging** - structlog
- **Metrics** - Prometheus
- **Tracing** - OpenTelemetry
- **Error tracking** - Sentry

## Будущие улучшения

### Phase 2
- [ ] Tagging system (filter questions by tags)
- [ ] Spaced repetition algorithm
- [ ] Code execution sandbox (для проверки кода)
- [ ] AI feedback на ответы

### Phase 3
- [ ] Multi-user support
- [ ] Social features (share questions)
- [ ] Mobile app
- [ ] Integration с GitHub для auto-check

## Заключение

Архитектура спроектирована для:
- ✅ Быстрого локального запуска
- ✅ Легкой модификации и расширения
- ✅ Минимальных зависимостей
- ✅ Хорошей структурированности кода
- ✅ Potential для масштабирования

