# Формат файлов с вопросами для Deep Learning Platform

Этот файл объясняет, как создавать .md файлы с вопросами для импорта в платформу.

## Два формата

Платформа поддерживает **два формата**: простой (для обычных вопросов) и многоуровневый (для прогрессивного изучения концептов).

---

## Формат 1: Простой (Basic Questions)

Используй для обычных независимых вопросов.

### Структура:

```markdown
# Topic: Название темы

## Question: Название вопроса
**Difficulty**: Easy|Medium|Hard
**Type**: Text|Code

Текст вопроса с объяснениями и примерами кода...

**Answer**:
Правильный ответ с объяснениями...

---

## Question: Следующий вопрос
...
```

### Пример:

```markdown
# Topic: Python Web3 Basics

## Question: Подключение к Ethereum Node
**Difficulty**: Easy
**Type**: Code

Как подключиться к Ethereum node через web3.py и получить balance кошелька?

**Answer**:
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_KEY'))
address = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
balance = w3.eth.get_balance(address)
balance_eth = w3.from_wei(balance, 'ether')
print(f"Balance: {balance_eth} ETH")
```
\```

---

## Question: Вызов view функции
**Difficulty**: Easy
**Type**: Code

Как вызвать read-only функцию `getValue()` из смарт-контракта?

**Answer**:
```python
contract = w3.eth.contract(address=contract_address, abi=abi)
value = contract.functions.getValue().call()
```

`.call()` используется для view/pure функций (бесплатно, не требует gas).
```

---

## Формат 2: Многоуровневый (Progressive Concepts)

Используй для глубокого изучения одного концепта с постепенным усложнением.

### Структура:

```markdown
# Topic: Название темы

## Concept: Название концепта
**Tags**: tag1, tag2, tag3
**Estimated Time**: XX minutes

### Level 1: Название первого уровня (Surface)
Вопрос для начинающих...

**Answer**:
Простой ответ...

### Level 2: Название второго уровня (Deeper)
Более сложный вопрос...

**Answer**:
Более детальный ответ...

### Level 3: Название третьего уровня (Expert)
Экспертный вопрос...

**Answer**:
Глубокий ответ с нюансами...

### Level 4: Название четвертого уровня (Master)
Вопрос для мастеров...

**Answer**:
Максимально детальный ответ...

**Resources**:
- [Video] URL - Название
- [Article] URL - Название
- [Code] URL - Название
- [Tool] URL - Название
- [Docs] URL - Название

**Related Concepts**: Concept 1, Concept 2, Concept 3

---

## Concept: Следующий концепт
...
```

### Пример:

```markdown
# Topic: Solidity Security

## Concept: Reentrancy Attacks
**Tags**: security, vulnerabilities, CEI-pattern, exploits
**Estimated Time**: 25 minutes

### Level 1: Что такое reentrancy?
Объясни простыми словами, что такое reentrancy attack в Solidity.

**Answer**:
Reentrancy - это когда внешний контракт может повторно вызвать функцию до завершения первого вызова. Злоумышленник может "переввать" функцию и украсть средства.

Пример уязвимого кода:
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    msg.sender.call{value: amount}("");  // ⚠️ Внешний вызов до обновления state
    balances[msg.sender] = 0;
}
```
\```

### Level 2: Как работает CEI pattern?
Объясни Checks-Effects-Interactions pattern и как он защищает от reentrancy.

**Answer**:
CEI pattern - это порядок выполнения:
1. **Checks** - проверки условий
2. **Effects** - изменение state
3. **Interactions** - внешние вызовы

Правильный код:
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    require(amount > 0, "No balance");     // 1. Checks
    balances[msg.sender] = 0;              // 2. Effects
    msg.sender.call{value: amount}("");    // 3. Interactions
}
```
\```

Баланс обнуляется ДО отправки средств, поэтому повторный вызов не сработает.

### Level 3: Cross-contract reentrancy
Что такое cross-contract reentrancy и как от него защититься?

**Answer**:
Cross-contract reentrancy происходит когда state разделяется между несколькими контрактами.

Пример:
```solidity
// ContractA
function withdraw() public {
    uint amount = sharesInA[msg.sender];
    sharesInA[msg.sender] = 0;
    msg.sender.call{value: amount}("");
}

// ContractB использует то же sharesInA!
function transfer(address to, uint amount) public {
    sharesInA[msg.sender] -= amount;
    sharesInA[to] += amount;
}
```
\```

Защита:
- ReentrancyGuard от OpenZeppelin (global lock)
- Независимые state переменные
- Pull over Push pattern

### Level 4: Read-only reentrancy
Объясни read-only reentrancy на примере Curve exploit.

**Answer**:
Read-only reentrancy - когда view функции используют устаревшее состояние во время reentrancy.

Пример (упрощенно):
```solidity
contract Vault {
    function withdraw() public {
        uint shares = balanceOf[msg.sender];
        token.transfer(msg.sender, shares);  // Внешний вызов
        balanceOf[msg.sender] = 0;           // Обновление после
    }
    
    function getPrice() public view returns (uint) {
        return totalAssets / totalShares;    // Использует старое состояние!
    }
}
```
\```

Во время `token.transfer()` злоумышленник вызывает `getPrice()` который вернет завышенную цену, так как `balanceOf` еще не обновлен.

Защита:
- ReentrancyGuard даже на view функциях
- Обновлять state перед внешними вызовами
- Использовать reentrancy-aware oracles

**Resources**:
- [Video] https://youtube.com/watch?v=4Mm3BCyHtDY - Smart Contract Programmer: Reentrancy Attack
- [Article] https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/ - Consensys Security Guide
- [Code] https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/security/ReentrancyGuard.sol - ReentrancyGuard Implementation
- [Article] https://blog.openzeppelin.com/reentrancy-after-istanbul - Read-only Reentrancy Post-mortem

**Related Concepts**: CEI Pattern, State Mutations, Gas Optimization, Flash Loan Attacks
```

---

## Правила и рекомендации

### ✅ DO (Делай так):

1. **Реальные вопросы** - используй вопросы, которые встречаются на интервью или в реальной разработке
2. **Детальные ответы** - объясняй "почему", а не только "как"
3. **Код с комментариями** - добавляй комментарии к сложным местам
4. **Практические примеры** - показывай реальные use cases
5. **Ошибки и edge cases** - объясняй что может пойти не так
6. **Сравнения** - "в чем разница между X и Y?"
7. **Ссылки на код** - давай ссылки на реальные реализации (OpenZeppelin, Uniswap, etc.)

### ❌ DON'T (Не делай так):

1. **Не используй тривиальные вопросы** - "что такое integer", "что такое variable"
2. **Не давай односложные ответы** - всегда объясняй контекст
3. **Не пиши абстракции** - конкретные примеры лучше
4. **Не пропускай edge cases** - они часто спрашиваются на интервью
5. **Не используй устаревшие практики** - только актуальные подходы
6. **Не копируй определения из документации** - объясняй своими словами

### Difficulty Guidelines:

- **Easy** - базовые концепты, синтаксис, простые операции (15-20% вопросов)
- **Medium** - практическое применение, паттерны, debugging (50-60% вопросов)
- **Hard** - оптимизация, security, edge cases, архитектура (20-30% вопросов)

### Level Guidelines (для многоуровневых):

- **Level 1** - "Что это?" (определение, базовое понимание)
- **Level 2** - "Как это работает?" (механика, примеры использования)
- **Level 3** - "Продвинутое использование" (edge cases, оптимизация)
- **Level 4** - "Глубокое понимание" (internals, exploits, real-world scenarios)

### Tags Guidelines:

Хорошие tags для категоризации:
- Техническая область: `security`, `optimization`, `testing`, `deployment`
- Паттерны: `design-patterns`, `best-practices`, `anti-patterns`
- Технологии: `web3`, `ethers`, `hardhat`, `foundry`, `remix`
- Концепты: `gas`, `storage`, `memory`, `calldata`, `abi`

---

## Шаблоны для копирования

### Шаблон простого файла:

```markdown
# Topic: [Название темы]

## Question: [Название вопроса]
**Difficulty**: [Easy|Medium|Hard]
**Type**: [Text|Code]

[Текст вопроса]

**Answer**:
[Ответ с объяснениями]

---
```

### Шаблон многоуровневого файла:

```markdown
# Topic: [Название темы]

## Concept: [Название концепта]
**Tags**: [tag1, tag2, tag3]
**Estimated Time**: [X minutes]

### Level 1: [Вопрос для начинающих]
[Текст вопроса]

**Answer**:
[Простой ответ]

### Level 2: [Углубленный вопрос]
[Текст вопроса]

**Answer**:
[Детальный ответ]

### Level 3: [Экспертный вопрос]
[Текст вопроса]

**Answer**:
[Глубокий ответ]

### Level 4: [Мастерский вопрос]
[Текст вопроса]

**Answer**:
[Максимально детальный ответ]

**Resources**:
- [Video] [URL] - [Название]
- [Article] [URL] - [Название]
- [Code] [URL] - [Название]

**Related Concepts**: [Concept1, Concept2]

---
```

---

## Примеры тем для генерации

### Solidity:
- Reentrancy Attacks
- Gas Optimization Techniques
- Storage vs Memory vs Calldata
- Delegatecall and Proxy Patterns
- ERC Standards (20, 721, 1155)
- Upgradeable Contracts
- Assembly и Low-level Calls
- Events and Logging
- Modifiers и Access Control
- Integer Overflow/Underflow

### Python + Web3:
- Connecting to Nodes
- Reading Contract State
- Sending Transactions
- Event Listening
- Gas Estimation
- Signing Messages
- HD Wallets
- Transaction Debugging
- ABIs and Contract Interaction
- MEV and Flashbots

### Blockchain Theory:
- Consensus Mechanisms
- Merkle Trees
- Transaction Lifecycle
- Gas Mechanics
- Block Structure
- Finality
- Light Clients
- State Management
- Cryptographic Primitives
- P2P Networking

---

## Prompt для нейронки

Можешь использовать такой промпт:

```
Создай файл с вопросами для Deep Learning Platform в многоуровневом формате.

Тема: [укажи тему, например "Solidity Gas Optimization"]

Требования:
- 3-5 концептов по теме
- Каждый концепт с 3-4 уровнями (L1-L4)
- Реальные вопросы, которые встречаются на интервью
- Детальные ответы с примерами кода
- Добавь tags для каждого концепта
- Добавь ресурсы (ссылки на документацию, статьи, видео)
- Указывай related concepts

Формат следуй строго по FORMAT.md из репозитория.
Не используй тривиальные вопросы типа "что такое переменная".
Фокус на практическом применении и реальных сценариях.
```

---

## Проверка перед импортом

Убедись что:
- [ ] Есть `# Topic:` в начале
- [ ] Для многоуровневых: есть `## Concept:`
- [ ] Для простых: есть `## Question:`
- [ ] Каждый вопрос имеет `**Answer**:`
- [ ] Code blocks используют правильный синтаксис (\`\`\`language)
- [ ] Resources в правильном формате: `- [Type] URL - Title`
- [ ] Related Concepts через запятую

---

## Полезные ссылки

- OpenZeppelin Contracts: https://github.com/OpenZeppelin/openzeppelin-contracts
- Solidity Docs: https://docs.soliditylang.org/
- Web3.py Docs: https://web3py.readthedocs.io/
- Ethereum.org: https://ethereum.org/developers
- Consensys Security Best Practices: https://consensys.github.io/smart-contract-best-practices/

---

Создано для Deep Learning Platform v2.0

