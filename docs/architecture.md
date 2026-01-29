# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                 │
├─────────────┬─────────────┬─────────────────────────────────────┤
│   Web UI    │    CLI      │   Cursor/IDE (terminal)             │
│  (browser)  │  (Python)   │   (same CLI)                        │
└──────┬──────┴──────┬──────┴──────────────┬──────────────────────┘
       │             │                      │
       ▼             ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                │
│                   FastAPI (Python)                              │
│  ┌────────────┬────────────┬────────────┬────────────────────┐  │
│  │   /auth    │  /session  │  /analyze  │     /export        │  │
│  └────────────┴────────────┴────────────┴────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐
│  LLM Layer  │    │  RAG Layer  │    │   Storage Layer     │
│             │    │             │    │                     │
│ OpenRouter  │    │  ChromaDB   │    │  PostgreSQL (users) │
│ Claude/GPT  │    │ (vectors)   │    │  S3/MinIO (files)   │
└─────────────┘    └─────────────┘    └─────────────────────┘
```

## Components

### 1. API Gateway (FastAPI)

```
backend/
├── app/
│   ├── main.py              # Entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── dependencies.py      # DI container
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py      # JWT auth
│   │   │   ├── sessions.py  # Learning sessions CRUD
│   │   │   ├── analyze.py   # LLM analysis endpoints
│   │   │   └── export.py    # MD/JSON export
│   │   └── router.py
│   │
│   ├── services/
│   │   ├── llm.py           # OpenRouter client
│   │   ├── rag.py           # ChromaDB operations
│   │   ├── prompts.py       # Prompt templates
│   │   └── session.py       # Session logic
│   │
│   ├── models/
│   │   ├── user.py          # SQLAlchemy models
│   │   ├── session.py
│   │   └── schemas.py       # Pydantic schemas
│   │
│   └── core/
│       ├── security.py      # JWT, hashing
│       └── exceptions.py
│
├── alembic/                 # Migrations
├── tests/
├── Dockerfile
└── pyproject.toml
```

### 2. LLM Layer

```python
# Абстракция над провайдерами
class LLMProvider(Protocol):
    async def generate(self, prompt: str, **kwargs) -> str: ...
    async def embed(self, text: str) -> list[float]: ...

# Реализации
class OpenRouterProvider(LLMProvider):
    """Claude, GPT, Llama через OpenRouter API"""
    
class AnthropicProvider(LLMProvider):
    """Direct Claude API"""
```

**Конфиг выбора модели**:
```yaml
llm:
  provider: openrouter  # openrouter | anthropic | openai
  model: claude-3-5-sonnet
  fallback: gpt-4o-mini
  embedding_model: text-embedding-3-small
```

### 3. RAG Layer (ChromaDB)

```
chromadb/
├── collections/
│   ├── user_{id}_sessions     # Все сессии юзера
│   └── user_{id}_knowledge    # Накопленные знания
```

**Embedding strategy**:
- Chunk size: 512 tokens
- Overlap: 50 tokens
- Metadata: topic, iteration, timestamp, gap_score

### 4. Storage Layer

**PostgreSQL** (users, sessions metadata):
```sql
users (id, email, password_hash, created_at)
sessions (id, user_id, topic, status, created_at)
iterations (id, session_id, number, questions_json, answers_json, analysis_json)
```

**S3/MinIO** (markdown exports, optional):
```
bucket/
├── {user_id}/
│   ├── exports/
│   │   └── cap-theorem-2026-01.md
│   └── imports/
│       └── obsidian-vault.zip
```

## Data Flow

### Start Session
```
1. User: "CAP theorem", level="junior"
2. API: Check RAG for prior knowledge on topic
3. LLM: Generate 10 questions (considering prior knowledge)
4. Store: Create session + iteration in DB
5. Return: Questions array
```

### Submit Answer
```
1. User: Answer to Q1
2. RAG: Fetch relevant prior answers
3. LLM: Analyze depth (not correctness)
4. LLM: Identify gaps
5. Store: Save answer + analysis
6. RAG: Index answer for future retrieval
7. Return: Gaps + next question (or drill-down)
```

### Analyze Session
```
1. Fetch all iterations for session
2. LLM: Generate summary of progress
3. LLM: Identify persistent gaps
4. Store: Update session analysis
5. Return: Progress report + recommendations
```

## Scalability Considerations

### 100 users (current)
- Single instance FastAPI
- ChromaDB in Docker (local persistence)
- PostgreSQL single instance
- No caching needed

### 1000+ users (future)
- Add Redis for caching LLM responses
- ChromaDB → Qdrant (distributed)
- PostgreSQL → connection pooling (pgbouncer)
- Rate limiting per user

## Security

- JWT tokens (access + refresh)
- Password hashing: argon2
- API rate limiting: 60 req/min per user
- LLM API keys: server-side only
- CORS: whitelist frontend domain

## Error Handling

```python
# Structured errors
class AppError(Exception):
    code: str
    message: str
    details: dict

# LLM fallback
async def generate_with_fallback(prompt):
    try:
        return await primary_llm.generate(prompt)
    except RateLimitError:
        return await fallback_llm.generate(prompt)
```






