# Neo4j Knowledge Graph Schema

## Описание

Схема графа знаний для Socratic Learning System. Граф отслеживает:

- **Концепты** (Concept) — понятия, которые изучает пользователь
- **Связи между концептами** — как понятия связаны друг с другом
- **Прогресс пользователя** — насколько освоен каждый концепт
- **Blind zones** — что пользователь упустил или недопонял

## Структура

### Узлы (Nodes)

1. **User** — пользователь системы
2. **Concept** — концепт/понятие (например, "CAP Theorem")
3. **Topic** — тема обучения (например, "Distributed Systems")
4. **Session** — учебная сессия

### Связи (Relationships)

1. **User -[KNOWS]-> Concept** — пользователь знает концепт (с уровнем mastery)
2. **Concept -[RELATES_TO]-> Concept** — связь между концептами
3. **Concept -[PREREQUISITE_FOR]-> Concept** — зависимость знаний
4. **User -[PARTICIPATED_IN]-> Session** — участие в сессии
5. **Session -[EXPLORED]-> Concept** — концепты, обсуждавшиеся в сессии
6. **Topic -[CONTAINS]-> Concept** — концепты внутри темы

## Использование

### Инициализация схемы

```bash
# Запустить Neo4j через docker-compose
docker-compose up -d neo4j

# Применить схему (constraints, indexes, sample data)
docker-compose exec neo4j cypher-shell -u neo4j -p socratic_graph_2024 \
  -f /var/lib/neo4j/import/knowledge_graph_schema.cypher
```

### Проверка

```bash
# Проверить что схема применена
docker-compose exec neo4j cypher-shell -u neo4j -p socratic_graph_2024 \
  "SHOW CONSTRAINTS;"

# Посмотреть sample data
docker-compose exec neo4j cypher-shell -u neo4j -p socratic_graph_2024 \
  "MATCH (n) RETURN labels(n), count(n);"
```

### Browser UI

Откройте http://localhost:7474 и войдите:
- Username: `neo4j`
- Password: `socratic_graph_2024`

## Примеры запросов

### Получить все концепты пользователя

```cypher
MATCH (u:User {user_id: 'test-user-001'})-[k:KNOWS]->(c:Concept)
RETURN c.name, k.mastery_level, k.last_interaction
ORDER BY k.mastery_level DESC;
```

### Найти blind zones

```cypher
MATCH (u:User {user_id: 'test-user-001'})-[k:KNOWS]->(c1:Concept)-[r:RELATES_TO]->(c2:Concept)
WHERE k.mastery_level > 0.7 AND NOT EXISTS {
  MATCH (u)-[:KNOWS]->(c2)
}
RETURN c2.name AS blind_zone, c1.name AS known_concept, r.relationship_type
ORDER BY r.strength DESC;
```

### Визуализировать граф пользователя

```cypher
MATCH path = (u:User {user_id: 'test-user-001'})-[:KNOWS]->(c:Concept)-[:RELATES_TO*0..2]->()
RETURN path
LIMIT 50;
```

## Масштабирование

- **Индексы** созданы для быстрого поиска по user_id, concept_id, topic_id
- **Full-text search** по названиям концептов
- Для графов >10K узлов рекомендуется Neo4j Enterprise с clustering

