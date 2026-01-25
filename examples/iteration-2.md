# Learning Session: CAP Theorem - Iteration 2

**Date**: 2026-01-26
**Iteration**: 2
**Focus**: Partition tolerance mechanisms + Conflict resolution

## Focus Areas
- partition tolerance implementation
- eventual consistency механизмы
- BFT vs CFT различия

---

## Deep-Dive Questions

### Q1: Network partition mechanics
У тебя blockchain с 5 nodes. Network partition разделяет их на группы [A,B] и [C,D,E].
Что происходит на уровне протокола в следующих случаях:
a) Ethereum (AP)
b) Hyperledger с PBFT (CP)

Опиши шаг за шагом.

**Твой ответ:**


---

### Q2: Quorum и split-brain
Что такое quorum? Почему в distributed systems нужно нечетное количество nodes?
Объясни split-brain problem и как его избежать.

**Твой ответ:**


---

### Q3: Uncle blocks в Ethereum
Ты упомянул что Ethereum может форкнуться. 
- Что такое uncle block?
- Почему майнеры получают reward за uncle blocks?
- Как это связано с partition tolerance?

**Твой ответ:**


---

### Q4: Conflict resolution strategies
В eventual consistency системе два node одновременно обновили один record.
Опиши 3 стратегии conflict resolution. Когда какую использовать?

**Твой ответ:**


---

### Q5: Byzantine vs Crash faults
В чем принципиальная разница между:
- Byzantine Fault Tolerance (BFT)
- Crash Fault Tolerance (CFT)

Какие протоколы используют что и почему?

**Твой ответ:**


---

## Практические задачи

### Task 1: Симуляция partition
Напиши псевдокод для simple consensus protocol, который:
- Работает с 3 nodes
- Использует quorum (2 из 3)
- Обрабатывает network partition

```python
# твой код
```

---

### Task 2: Design decision
Проектируешь voting system на blockchain:
- Каждый голос критичен (double-voting недопустим)
- Система должна работать если 1 из 3 regions offline
- Нужна audit trail

Какой CAP выбор делаешь? Обоснуй архитектуру.

**Твой дизайн:**


---

### Task 3: Code review
```solidity
contract SimpleVoting {
    mapping(address => bool) public voted;
    uint public voteCount;
    
    function vote() public {
        require(!voted[msg.sender], "Already voted");
        voted[msg.sender] = true;
        voteCount++;
    }
}
```

Этот контракт deployed на Ethereum. Какие CAP-related проблемы видишь?
Что происходит при chain reorg?

**Твой анализ:**


---

## После заполнения
```bash
./learn.sh analyze examples/iteration-2.md
```

