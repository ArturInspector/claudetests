// ===================================================================
// Socratic Learning System - Knowledge Graph Schema
// ===================================================================
// Структура графа для отслеживания знаний пользователя
//
// Основные сущности:
// - User: пользователь системы
// - Concept: концепт/понятие (например, "CAP theorem", "Partition tolerance")
// - Topic: тема обучения (например, "Distributed Systems")
// - Session: учебная сессия

// -------------------------------------------------------------------
// 1. CONSTRAINTS (уникальность и обязательные поля)
// -------------------------------------------------------------------

// User constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

// Concept constraints
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;

// Topic constraints
CREATE CONSTRAINT topic_id_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;

// Session constraints
CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.session_id IS UNIQUE;

// -------------------------------------------------------------------
// 2. INDEXES (ускорение поиска)
// -------------------------------------------------------------------

// Full-text search по названиям концептов
CREATE FULLTEXT INDEX concept_name_fulltext IF NOT EXISTS
FOR (c:Concept) ON EACH [c.name, c.description];

// Index для поиска концептов по теме
CREATE INDEX concept_topic_idx IF NOT EXISTS
FOR (c:Concept) ON (c.topic_id);

// Index для temporal queries (когда концепт был освоен)
CREATE INDEX concept_mastered_at_idx IF NOT EXISTS
FOR (c:Concept) ON (c.mastered_at);

// -------------------------------------------------------------------
// 3. NODE LABELS & PROPERTIES
// -------------------------------------------------------------------

// User Node
// Свойства:
// - user_id: string (UUID из PostgreSQL)
// - created_at: datetime
// - total_sessions: integer

// Concept Node
// Свойства:
// - concept_id: string (UUID)
// - name: string (например, "Partition Tolerance")
// - description: string (краткое описание)
// - topic_id: string (связь с темой)
// - mastery_level: float (0.0 - 1.0, насколько освоен)
// - first_seen_at: datetime (когда впервые упомянут)
// - last_reviewed_at: datetime (последний раз когда обсуждался)
// - mastered_at: datetime | null (когда достигнут mastery_level >= 0.8)
// - times_reviewed: integer (сколько раз пересматривался)

// Topic Node
// Свойства:
// - topic_id: string (UUID)
// - name: string (например, "Distributed Systems")
// - created_at: datetime

// Session Node
// Свойства:
// - session_id: string (UUID из PostgreSQL)
// - topic_name: string
// - started_at: datetime
// - completed_at: datetime | null
// - total_questions: integer

// -------------------------------------------------------------------
// 4. RELATIONSHIP TYPES
// -------------------------------------------------------------------

// User -> Concept (KNOWS)
// Свойства:
// - mastery_level: float (0.0 - 1.0)
// - confidence: float (0.0 - 1.0, насколько уверен пользователь)
// - last_interaction: datetime
// - interaction_count: integer

// Concept -> Concept (RELATES_TO)
// Свойства:
// - strength: float (0.0 - 1.0, насколько сильна связь)
// - relationship_type: string ("prerequisite", "similar", "opposite", "example_of")
// - discovered_in_session: string (session_id)
// - created_at: datetime

// Concept -> Concept (PREREQUISITE_FOR)
// Специальный тип для зависимостей знаний
// Свойства:
// - required_mastery: float (минимальный mastery_level для прогресса)

// User -> Session (PARTICIPATED_IN)
// Свойства:
// - started_at: datetime
// - completed_at: datetime | null

// Session -> Concept (EXPLORED)
// Свойства:
// - mentioned_count: integer (сколько раз упоминался в сессии)
// - mastery_delta: float (изменение понимания за сессию)
// - timestamp: datetime

// Topic -> Concept (CONTAINS)
// Свойства:
// - importance: float (0.0 - 1.0, важность концепта в теме)

// -------------------------------------------------------------------
// 5. SAMPLE DATA (для тестирования)
// -------------------------------------------------------------------

// Создание тестового пользователя
MERGE (u:User {user_id: 'test-user-001'})
SET u.created_at = datetime(),
    u.total_sessions = 0;

// Создание темы Distributed Systems
MERGE (t:Topic {topic_id: 'topic-distributed-systems'})
SET t.name = 'Distributed Systems',
    t.created_at = datetime();

// Создание базовых концептов
MERGE (c1:Concept {concept_id: 'concept-cap-theorem'})
SET c1.name = 'CAP Theorem',
    c1.description = 'Невозможно одновременно гарантировать Consistency, Availability и Partition Tolerance',
    c1.topic_id = 'topic-distributed-systems',
    c1.mastery_level = 0.0,
    c1.first_seen_at = datetime(),
    c1.times_reviewed = 0;

MERGE (c2:Concept {concept_id: 'concept-partition-tolerance'})
SET c2.name = 'Partition Tolerance',
    c2.description = 'Система продолжает работать при сетевых разрывах',
    c2.topic_id = 'topic-distributed-systems',
    c2.mastery_level = 0.0,
    c2.first_seen_at = datetime(),
    c2.times_reviewed = 0;

MERGE (c3:Concept {concept_id: 'concept-consistency'})
SET c3.name = 'Consistency',
    c3.description = 'Все узлы видят одни и те же данные одновременно',
    c3.topic_id = 'topic-distributed-systems',
    c3.mastery_level = 0.0,
    c3.first_seen_at = datetime(),
    c3.times_reviewed = 0;

MERGE (c4:Concept {concept_id: 'concept-availability'})
SET c4.name = 'Availability',
    c4.description = 'Каждый запрос получает ответ (success/failure)',
    c4.topic_id = 'topic-distributed-systems',
    c4.mastery_level = 0.0,
    c4.first_seen_at = datetime(),
    c4.times_reviewed = 0;

// Создание связей между концептами
MERGE (c2)-[r1:RELATES_TO]->(c1)
SET r1.strength = 0.9,
    r1.relationship_type = 'component_of',
    r1.created_at = datetime();

MERGE (c3)-[r2:RELATES_TO]->(c1)
SET r2.strength = 0.9,
    r2.relationship_type = 'component_of',
    r2.created_at = datetime();

MERGE (c4)-[r3:RELATES_TO]->(c1)
SET r3.strength = 0.9,
    r3.relationship_type = 'component_of',
    r3.created_at = datetime();

// Связь концептов с темой
MERGE (t)-[ct1:CONTAINS]->(c1)
SET ct1.importance = 1.0;

MERGE (t)-[ct2:CONTAINS]->(c2)
SET ct2.importance = 0.8;

MERGE (t)-[ct3:CONTAINS]->(c3)
SET ct3.importance = 0.8;

MERGE (t)-[ct4:CONTAINS]->(c4)
SET ct4.importance = 0.8;

// -------------------------------------------------------------------
// 6. HELPER QUERIES (примеры использования)
// -------------------------------------------------------------------

// Получить все концепты пользователя с mastery_level
// MATCH (u:User {user_id: $user_id})-[k:KNOWS]->(c:Concept)
// RETURN c.name, k.mastery_level, k.last_interaction
// ORDER BY k.mastery_level DESC;

// Найти blind zones (концепты с низким mastery в связанных темах)
// MATCH (u:User {user_id: $user_id})-[k:KNOWS]->(c1:Concept)-[r:RELATES_TO]->(c2:Concept)
// WHERE k.mastery_level > 0.7 AND NOT EXISTS {
//   MATCH (u)-[:KNOWS]->(c2)
// }
// RETURN c2.name AS blind_zone, c1.name AS known_concept, r.relationship_type
// ORDER BY r.strength DESC;

// Найти следующий концепт для изучения (prerequisites выполнены)
// MATCH (u:User {user_id: $user_id})-[k:KNOWS]->(c1:Concept)-[p:PREREQUISITE_FOR]->(c2:Concept)
// WHERE k.mastery_level >= p.required_mastery
// AND NOT EXISTS {
//   MATCH (u)-[:KNOWS]->(c2)
// }
// RETURN c2.name, c2.description, COUNT(c1) as ready_prerequisites
// ORDER BY ready_prerequisites DESC;

