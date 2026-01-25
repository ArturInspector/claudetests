# Learning Session: CAP Theorem in Distributed Systems

**Date**: 2026-01-25
**Iteration**: 1
**Level**: junior, знаю базу БД

## Questions

### Q1: Базовое понимание
Объясни CAP theorem своими словами.

**Твой ответ:**
CAP - это про то что в распределенной системе нельзя одновременно иметь все три свойства: Consistency, Availability, Partition tolerance. Можно выбрать только два.

---

### Q2: Компоненты
Что означает каждая буква в CAP?

**Твой ответ:**
C - Consistency: все ноды видят одинаковые данные
A - Availability: система всегда отвечает на запросы
P - Partition tolerance: система работает даже если связь между нодами нарушена

---

### Q3: Blockchain контекст
Как CAP применяется к blockchain?

**Твой ответ:**
Ethereum выбирает AP - доступность и partition tolerance, жертвуя consistency (eventual consistency через consensus).
Hyperledger может быть CP - consistency и partition tolerance.

---

### Q4: Trade-offs
Какие практические последствия выбора AP vs CP?

**Твой ответ:**
AP - система быстрая, но могут быть временные inconsistencies
CP - данные всегда consistent, но при network partition система может стать недоступной

---

### Q5: Consensus algorithms
Как Proof-of-Work связан с CAP?

**Твой ответ:**
PoW - это способ достичь consensus в AP системе. Блокчейн может форкнуться (partition), но eventually один chain wins.

---

### Q6: Ethereum специфика
Почему Ethereum выбрал AP?

**Твой ответ:**
Для decentralization нужна availability - любая нода может работать даже если отрезана от других. Consistency достигается через longest chain rule.

---

### Q7: Network partition
Что происходит при network partition в Ethereum?

**Твой ответ:**
Образуются два форка, каждый продолжает работать. Когда partition решается, короткий fork отбрасывается.

---

### Q8: Byzantine Fault Tolerance
Как BFT связан с CAP?

**Твой ответ:**
BFT - это про consensus в присутствии malicious nodes. Это дополнительное требование поверх CAP.

---

### Q9: Практический дизайн
Спроектируй blockchain для supply chain с учетом CAP.

**Твой ответ:**
Supply chain нужна consistency (чтобы все видели одинаковое состояние товаров).
Выбираю CP подход:
- Permissioned blockchain (Hyperledger)
- Strong consistency через PBFT consensus
- Trade-off: если большинство nodes недоступны, система останавливается

---

### Q10: Edge case
Что если нужны И consistency И availability?

**Твой ответ:**
Нельзя в pure distributed system. Но можно:
- Single node (не distributed)
- Или eventual consistency с conflict resolution
- Или hybrid approach с разными гарантиями для разных операций

---

## Запуск анализа
```bash
./learn.sh analyze examples/cap-theorem-session.md
```

