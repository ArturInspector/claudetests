# Topic: Solidity Advanced

## Question: Reentrancy Attack Prevention
**Difficulty**: Medium
**Type**: Code

Что не так с этим кодом и как его исправить?

```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    msg.sender.call{value: amount}("");
    balances[msg.sender] = 0;
}
```

**Answer**:
Reentrancy уязвимость - баланс обнуляется ПОСЛЕ отправки средств, что позволяет повторно вызвать функцию до обнуления.

Правильный вариант (Checks-Effects-Interactions pattern):
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    balances[msg.sender] = 0;  // Обнуляем ДО отправки
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

Или использовать ReentrancyGuard от OpenZeppelin:
```solidity
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

function withdraw() public nonReentrant {
    uint amount = balances[msg.sender];
    balances[msg.sender] = 0;
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

---

## Question: Gas Optimization
**Difficulty**: Hard
**Type**: Code

Как оптимизировать этот код для экономии gas?

```solidity
uint[] public values;

function sum() public view returns (uint) {
    uint total = 0;
    for (uint i = 0; i < values.length; i++) {
        total += values[i];
    }
    return total;
}
```

**Answer**:
Несколько оптимизаций:

1. Кэшировать `values.length` (каждое обращение стоит gas)
2. Использовать `unchecked` для инкремента (экономит ~30-40 gas на итерацию)
3. Кэшировать значение из storage в memory

Оптимизированный код:
```solidity
function sum() public view returns (uint) {
    uint total = 0;
    uint len = values.length;
    
    for (uint i = 0; i < len;) {
        total += values[i];
        unchecked { i++; }
    }
    
    return total;
}
```

Еще лучше - если массив большой, кэшировать в memory:
```solidity
function sum() public view returns (uint) {
    uint[] memory vals = values;  // Одно чтение из storage
    uint total = 0;
    uint len = vals.length;
    
    for (uint i = 0; i < len;) {
        total += vals[i];
        unchecked { i++; }
    }
    
    return total;
}
```

---

## Question: msg.sender vs tx.origin
**Difficulty**: Medium
**Type**: Text

В чем разница между `msg.sender` и `tx.origin`? Когда использование `tx.origin` опасно?

**Answer**:
**msg.sender** - адрес непосредственного вызывающего (может быть контракт или EOA)

**tx.origin** - адрес EOA, который инициировал транзакцию (всегда EOA, не контракт)

Пример:
```
User (0xAAA) -> Contract A -> Contract B
В Contract B:
  msg.sender = 0x...A (адрес Contract A)
  tx.origin = 0xAAA (адрес User)
```

**Почему tx.origin опасен:**

Phishing атака:
```solidity
// Vulnerable contract
function transfer(address to, uint amount) public {
    require(tx.origin == owner);  // ПЛОХО!
    balances[to] += amount;
}
```

Злоумышленник создает контракт:
```solidity
function attack() public {
    vulnerableContract.transfer(attacker, 1000);
}
```

Если owner вызовет `attack()`, проверка `tx.origin == owner` пройдет, и средства будут украдены!

**Правильно:** всегда используй `msg.sender` для проверки авторизации.

---

## Question: Storage vs Memory vs Calldata
**Difficulty**: Medium
**Type**: Text

Объясни разницу между `storage`, `memory` и `calldata` для массивов и строк. Когда что использовать?

**Answer**:

**storage** - постоянное хранилище на блокчейне
- Самое дорогое (gas)
- Данные сохраняются между вызовами
- Может быть изменено
```solidity
uint[] storage myArray;  // Ссылка на storage переменную
```

**memory** - временная память на время выполнения функции
- Среднее по стоимости
- Данные удаляются после выполнения
- Может быть изменено
```solidity
function process(uint[] memory data) public {
    data[0] = 100;  // Можно изменять
}
```

**calldata** - неизменяемая область для входных параметров
- Самое дешевое!
- Только для входных параметров external функций
- НЕ может быть изменено
```solidity
function process(uint[] calldata data) external {
    // data[0] = 100;  // ERROR! Нельзя изменять
    uint value = data[0];  // Можно читать
}
```

**Когда использовать:**
- `storage` - для state variables и когда нужно изменять storage
- `memory` - для локальных переменных, которые нужно изменять
- `calldata` - для external функций, когда не нужно изменять данные (экономит gas!)

---

## Question: Events и их назначение
**Difficulty**: Easy
**Type**: Text

Зачем нужны events в Solidity? Как их слушать с помощью Python?

**Answer**:
**Зачем нужны events:**

1. **Логирование** - записывают данные в блокчейн (дешевле чем storage)
2. **Уведомления** - оффчейн приложения могут подписаться на события
3. **History** - можно восстановить историю изменений
4. **Поиск** - indexed параметры позволяют эффективно искать

Пример:
```solidity
event Transfer(address indexed from, address indexed to, uint256 value);

function transfer(address to, uint256 amount) public {
    balances[msg.sender] -= amount;
    balances[to] += amount;
    emit Transfer(msg.sender, to, amount);
}
```

**Как слушать с Python (web3.py):**

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# ABI контракта с event
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Создаем фильтр для события
event_filter = contract.events.Transfer.create_filter(
    fromBlock='latest',
    argument_filters={'from': user_address}  # Фильтр по indexed параметру
)

# Получаем события
events = event_filter.get_all_entries()
for event in events:
    print(f"From: {event.args['from']}")
    print(f"To: {event.args['to']}")
    print(f"Value: {event.args['value']}")

# Или слушаем в реальном времени
while True:
    for event in event_filter.get_new_entries():
        print(f"New transfer: {event.args}")
```

---

## Question: EIP-1559 Gas Mechanism
**Difficulty**: Medium
**Type**: Text

Что такое EIP-1559? Как изменилась структура fee после его внедрения?

**Answer**:
**EIP-1559** - обновление Ethereum (London fork, август 2021), которое изменило механизм оплаты gas.

**До EIP-1559:**
- Только `gasPrice` (цена за единицу gas)
- Fee = gasUsed × gasPrice
- Весь fee идет майнеру
- Проблема: непредсказуемость, аукционный механизм

**После EIP-1559:**
Два компонента:
1. **Base Fee** (базовая плата) - динамическая, сжигается (burn)
2. **Priority Fee (tip)** - чаевые майнеру

```
Total Fee = gasUsed × (baseFeePerGas + priorityFeePerGas)
```

Новые параметры транзакции:
- `maxFeePerGas` - максимум, что готов заплатить
- `maxPriorityFeePerGas` - максимальные чаевые

**Преимущества:**
- Предсказуемость (baseFee корректируется алгоритмом)
- Дефляция ETH (baseFee сжигается)
- Меньше переплат

**Пример с web3.py:**
```python
# До EIP-1559
tx = {
    'gasPrice': w3.eth.gas_price,
    'gas': 21000
}

# После EIP-1559
tx = {
    'maxFeePerGas': w3.eth.max_priority_fee + (2 * w3.eth.get_block('latest').baseFeePerGas),
    'maxPriorityFeePerGas': w3.eth.max_priority_fee,
    'gas': 21000
}
```

---

## Question: EOA vs Contract Account
**Difficulty**: Easy
**Type**: Text

В чем разница между EOA (Externally Owned Account) и Contract Account?

**Answer**:

**EOA (Externally Owned Account):**
- Управляется приватным ключом
- Может инициировать транзакции
- Не имеет кода
- Адрес получается из публичного ключа
- Примеры: MetaMask, Ledger

**Contract Account:**
- Управляется кодом (smart contract)
- НЕ может сам инициировать транзакции (только в ответ на вызов)
- Имеет код и storage
- Адрес вычисляется из адреса создателя и nonce
- Выполняет код при получении транзакции

**Ключевые отличия:**

| Характеристика | EOA | Contract |
|---------------|-----|----------|
| Приватный ключ | Да | Нет |
| Код | Нет | Да |
| Storage | Нет | Да |
| Может отправлять tx | Да | Нет (только через EOA) |
| Gas для создания | Бесплатно | Платно |

**Важно:** С EIP-4337 (Account Abstraction) и EIP-7702 границы размываются - можно делать "smart contract wallets" с расширенной логикой.

---

## Question: Merkle Tree в Ethereum
**Difficulty**: Hard
**Type**: Text

Что такое Merkle Tree и где он используется в Ethereum?

**Answer**:
**Merkle Tree (дерево Меркла)** - древовидная структура данных, где каждый лист - хеш данных, а каждая нода - хеш дочерних нод.

**Структура:**
```
        Root Hash
       /          \
    Hash01      Hash23
    /   \       /    \
  H0    H1    H2    H3
  |     |     |     |
 D0    D1    D2    D3
```

**Использование в Ethereum:**

1. **Transaction Tree** - все транзакции блока
2. **State Tree** - состояние всех аккаунтов (Patricia Merkle Tree)
3. **Receipt Tree** - результаты выполнения транзакций

**Зачем:**
- **Verification** - можно проверить включение транзакции без скачивания всего блока
- **Light clients** - могут работать только с headers
- **Proof of Inclusion** - Merkle Proof

**Практический пример - Airdrop:**
```solidity
contract MerkleAirdrop {
    bytes32 public merkleRoot;
    
    function claim(
        uint256 amount,
        bytes32[] calldata merkleProof
    ) external {
        bytes32 leaf = keccak256(abi.encodePacked(msg.sender, amount));
        require(MerkleProof.verify(merkleProof, merkleRoot, leaf), "Invalid proof");
        
        // Transfer tokens...
    }
}
```

Экономия gas: вместо хранения списка всех адресов (дорого), храним только один root hash!

**Python для создания Merkle Tree:**
```python
from web3 import Web3

def merkle_tree(leaves):
    if len(leaves) == 1:
        return leaves[0]
    
    next_level = []
    for i in range(0, len(leaves), 2):
        left = leaves[i]
        right = leaves[i+1] if i+1 < len(leaves) else leaves[i]
        next_level.append(Web3.keccak(left + right))
    
    return merkle_tree(next_level)
```

