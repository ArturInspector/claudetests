# Storage Design

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYERS                          │
├─────────────────┬───────────────────┬───────────────────┤
│   PostgreSQL    │     ChromaDB      │    File Storage   │
│   (structured)  │     (vectors)     │    (exports)      │
├─────────────────┼───────────────────┼───────────────────┤
│ Users           │ Session embeddings│ MD exports        │
│ Sessions        │ Knowledge base    │ Obsidian imports  │
│ Iterations      │ Prior answers     │ Attachments       │
│ Analytics       │                   │                   │
└─────────────────┴───────────────────┴───────────────────┘
```

## PostgreSQL Schema

### Core Tables

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    llm_preference JSONB DEFAULT '{"provider": "openrouter", "model": "claude-3-5-sonnet"}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(500) NOT NULL,
    level VARCHAR(50) DEFAULT 'junior',  -- junior, middle, senior
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed
    total_iterations INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Iterations within session
CREATE TABLE iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    number INT NOT NULL,
    focus_areas TEXT[],  -- from previous analysis
    questions JSONB NOT NULL,
    answers JSONB,       -- user answers
    analysis JSONB,      -- LLM analysis result
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indices
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_topic ON sessions USING gin(to_tsvector('english', topic));
CREATE INDEX idx_iterations_session ON iterations(session_id);
```

### JSONB Structures

```json
// iterations.questions
[
    {
        "id": "q1",
        "type": "conceptual",  // conceptual, practical, edge_case
        "difficulty": 1,       // 1-10
        "text": "Explain CAP theorem",
        "hints": ["Think about distributed systems"]
    }
]

// iterations.answers
{
    "q1": {
        "text": "CAP means...",
        "submitted_at": "2026-01-25T10:00:00Z",
        "time_spent_seconds": 120
    }
}

// iterations.analysis
{
    "understood": ["basic CAP definition"],
    "gaps": [
        {
            "area": "partition tolerance",
            "severity": "high",
            "reason": "no examples provided"
        }
    ],
    "score": {
        "depth": 6,
        "practical": 4,
        "clarity": 7
    },
    "next_focus": "partition tolerance mechanics",
    "generated_at": "2026-01-25T10:05:00Z"
}
```

### Analytics (future)

```sql
-- Track learning progress over time
CREATE TABLE progress_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    topic VARCHAR(500),
    depth_score INT,
    gaps_count INT,
    snapshot_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Aggregate gaps across sessions
CREATE MATERIALIZED VIEW user_gaps AS
SELECT 
    user_id,
    gap->>'area' as gap_area,
    COUNT(*) as occurrence_count,
    AVG((gap->>'severity_score')::int) as avg_severity
FROM iterations, 
     jsonb_array_elements(analysis->'gaps') as gap
GROUP BY user_id, gap->>'area';
```

## ChromaDB Collections

### Structure

```python
# Collection per user for isolation
collection_name = f"user_{user_id}_knowledge"

# Document structure
{
    "id": "iter_123_q1",
    "document": "User's answer text...",
    "metadata": {
        "session_id": "uuid",
        "topic": "CAP theorem",
        "question_id": "q1",
        "iteration": 1,
        "gap_score": 0.7,      # 0-1, how much gap detected
        "timestamp": 1706180000
    }
}
```

### Queries

```python
# Find similar past answers
results = collection.query(
    query_texts=["partition tolerance in distributed systems"],
    n_results=5,
    where={"topic": {"$eq": "CAP theorem"}}
)

# Find persistent gaps (answered poorly multiple times)
results = collection.query(
    query_texts=["network partitions"],
    n_results=10,
    where={"gap_score": {"$gte": 0.6}}
)
```

### Embedding Strategy

```python
CHUNK_CONFIG = {
    "chunk_size": 512,       # tokens
    "chunk_overlap": 50,     # tokens
    "embedding_model": "text-embedding-3-small"  # OpenAI
}

# Alternative: local embeddings (no API cost)
# "sentence-transformers/all-MiniLM-L6-v2"
```

## File Storage

### Local (Development)

```
storage/
├── exports/
│   └── {user_id}/
│       └── {session_slug}-{date}.md
└── imports/
    └── {user_id}/
        └── uploaded files
```

### S3/MinIO (Production)

```
bucket: socratic-learning
├── exports/{user_id}/{file}
├── imports/{user_id}/{file}
└── backups/daily/{date}.sql.gz
```

### Export Format (Markdown)

```markdown
# CAP Theorem - Learning Session

**Started**: 2026-01-25
**Iterations**: 3
**Status**: Completed

## Progress Summary
- Understanding: 8/10
- Gaps resolved: 5/7
- Time spent: 2h 15m

---

## Iteration 1

### Q1: Explain CAP theorem
**My Answer:**
CAP means consistency, availability, partition tolerance...

**Analysis:**
✅ Understood basic definition
❌ Gap: No real-world examples

---
[... more iterations ...]
```

## Data Lifecycle

### Retention

| Data Type | Retention | Notes |
|-----------|-----------|-------|
| Active sessions | Indefinite | User-controlled |
| Completed sessions | 2 years | Configurable |
| ChromaDB vectors | Same as session | Deleted with session |
| Exports | 90 days | User can re-export |

### Deletion Flow

```python
async def delete_session(session_id: UUID, user_id: UUID):
    # 1. Delete from ChromaDB
    await rag.delete_session_vectors(session_id)
    
    # 2. Delete from PostgreSQL (cascades to iterations)
    await db.execute("DELETE FROM sessions WHERE id = $1", session_id)
    
    # 3. Delete exports
    await storage.delete_session_exports(user_id, session_id)
```

## Backup Strategy

```yaml
# Daily backup cron
backup:
  postgres:
    schedule: "0 3 * * *"  # 3 AM daily
    retention: 30 days
    command: pg_dump | gzip > backup.sql.gz
    
  chromadb:
    schedule: "0 4 * * *"  # 4 AM daily
    retention: 14 days
    command: tar -czf chromadb-backup.tar.gz /data/chromadb
```

## Migration Path

### Obsidian Import

```python
async def import_obsidian_vault(user_id: UUID, zip_file: UploadFile):
    # 1. Extract markdown files
    md_files = extract_markdown(zip_file)
    
    # 2. Parse structure (folders = topics)
    topics = parse_vault_structure(md_files)
    
    # 3. Create sessions from files
    for topic, files in topics.items():
        session = await create_session(user_id, topic)
        
        # 4. Index content in ChromaDB
        for file in files:
            await rag.index_document(
                user_id=user_id,
                session_id=session.id,
                content=file.content,
                metadata={"source": "obsidian", "filename": file.name}
            )
```

### Obsidian Export

One-click export → `.md` file → drag to Obsidian vault. No plugins needed.






