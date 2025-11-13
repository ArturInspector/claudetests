# Topic: Python Web3 Development

## Question: Подключение к Ethereum Node
**Difficulty**: Easy
**Type**: Code

Как подключиться к Ethereum node и прочитать balance кошелька? Напиши код.

**Answer**:

```python
from web3 import Web3

# Подключение к node (можно использовать Infura, Alchemy, или локальный)
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_PROJECT_ID'))

# Проверка подключения
if not w3.is_connected():
    raise Exception("Failed to connect to Ethereum node")

print(f"Connected: {w3.is_connected()}")
print(f"Latest block: {w3.eth.block_number}")

# Адрес кошелька
address = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'

# Получить balance в Wei
balance_wei = w3.eth.get_balance(address)

# Конвертировать в ETH
balance_eth = w3.from_wei(balance_wei, 'ether')

print(f"Balance: {balance_eth} ETH")
```

**Альтернативы для подключения:**
```python
# Websocket (для real-time)
w3 = Web3(Web3.WebsocketProvider('wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID'))

# IPC (локальный node)
w3 = Web3(Web3.IPCProvider('/path/to/geth.ipc'))

# Testnet (Sepolia)
w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/YOUR_PROJECT_ID'))
```

---

## Question: Вызов Read-Only функции
**Difficulty**: Easy
**Type**: Code

Есть контракт с функцией `getValue() view returns (uint256)`. Как вызвать эту функцию через web3.py?

**Answer**:

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_PROJECT_ID'))

# Адрес контракта
contract_address = '0x...'

# ABI контракта (минимальный для getValue)
contract_abi = [
    {
        "inputs": [],
        "name": "getValue",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Создаем объект контракта
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Вызываем функцию (не требует gas, бесплатно)
value = contract.functions.getValue().call()

print(f"Value: {value}")
```

**С параметрами:**
```python
# Функция: balanceOf(address) view returns (uint256)
balance = contract.functions.balanceOf('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb').call()
```

**С указанием block:**
```python
# Получить значение на момент определенного блока
value_at_block = contract.functions.getValue().call(block_identifier=15000000)
```

**Важно:** `.call()` - для view/pure функций (не изменяют state, не требуют gas)

---

## Question: Отправка транзакции
**Difficulty**: Medium
**Type**: Code

Есть функция `setValue(uint256 _value)`. Как вызвать её с подписью транзакции?

**Answer**:

```python
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/YOUR_PROJECT_ID'))

# Твой приватный ключ (НИКОГДА не коммить в git!)
private_key = '0x...'
account = Account.from_key(private_key)

# Контракт
contract_address = '0x...'
contract_abi = [
    {
        "inputs": [{"type": "uint256", "name": "_value"}],
        "name": "setValue",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Строим транзакцию
transaction = contract.functions.setValue(42).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price,
    'chainId': 11155111  # Sepolia
})

# Подписываем
signed_txn = w3.eth.account.sign_transaction(transaction, private_key)

# Отправляем
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

print(f"Transaction hash: {tx_hash.hex()}")

# Ждем подтверждения
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Transaction mined in block {tx_receipt.blockNumber}")
print(f"Gas used: {tx_receipt.gasUsed}")
print(f"Status: {'Success' if tx_receipt.status == 1 else 'Failed'}")
```

**С EIP-1559:**
```python
transaction = contract.functions.setValue(42).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'maxFeePerGas': w3.to_wei(50, 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei(2, 'gwei'),
    'chainId': 1
})
```

---

## Question: Слушать Events в реальном времени
**Difficulty**: Medium
**Type**: Code

Как слушать events из смарт-контракта в реальном времени с помощью Python?

**Answer**:

**Способ 1: Polling (с HTTP provider)**
```python
from web3 import Web3
import time

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_PROJECT_ID'))

contract_address = '0x...'
contract_abi = [...]  # ABI с событием Transfer

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Создаем фильтр для события Transfer
event_filter = contract.events.Transfer.create_filter(fromBlock='latest')

# Polling loop
print("Listening for Transfer events...")
while True:
    for event in event_filter.get_new_entries():
        print(f"\nNew Transfer detected!")
        print(f"From: {event.args['from']}")
        print(f"To: {event.args['to']}")
        print(f"Value: {w3.from_wei(event.args['value'], 'ether')} tokens")
        print(f"Block: {event.blockNumber}")
        print(f"Tx: {event.transactionHash.hex()}")
    
    time.sleep(2)  # Проверяем каждые 2 секунды
```

**Способ 2: WebSocket (real-time, лучше)**
```python
from web3 import Web3
import asyncio

# WebSocket подключение
w3 = Web3(Web3.WebsocketProvider('wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID'))

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)

def handle_event(event):
    print(f"Transfer: {event.args['from']} -> {event.args['to']}")

# Запуск
event_filter = contract.events.Transfer.create_filter(fromBlock='latest')
asyncio.run(log_loop(event_filter, 2))
```

**С фильтрацией по indexed параметрам:**
```python
# Только трансферы ОТ определенного адреса
event_filter = contract.events.Transfer.create_filter(
    fromBlock='latest',
    argument_filters={'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'}
)
```

---

## Question: eth_call vs eth_sendTransaction
**Difficulty**: Medium
**Type**: Text

В чем разница между `eth_call` и `eth_sendTransaction`? Когда что использовать?

**Answer**:

**eth_call** (в web3.py - `.call()`)
- **Симуляция** выполнения без изменения state
- Не создает транзакцию в блокчейне
- Бесплатно (не тратит gas)
- Мгновенный результат
- Используется для view/pure функций

```python
# eth_call
balance = contract.functions.balanceOf(address).call()
```

**eth_sendTransaction** (в web3.py - `.transact()` или `.build_transaction()`)
- **Реальное** выполнение с изменением state
- Создает транзакцию в блокчейне
- Требует gas (платно)
- Нужно ждать майнинга
- Используется для функций, изменяющих state

```python
# eth_sendTransaction
tx_hash = contract.functions.transfer(to, amount).transact({
    'from': account.address
})
```

**Сравнение:**

| Характеристика | eth_call | eth_sendTransaction |
|---------------|----------|---------------------|
| Изменяет state | ❌ Нет | ✅ Да |
| Требует gas | ❌ Нет | ✅ Да |
| Требует подпись | ❌ Нет | ✅ Да |
| Записывается в блокчейн | ❌ Нет | ✅ Да |
| Скорость | Мгновенно | ~12 сек (block time) |
| Возвращает | Результат функции | Transaction hash |

**Частая ошибка:**
```python
# WRONG - call() не изменит state!
contract.functions.transfer(to, amount).call()

# RIGHT - используем transact()
tx_hash = contract.functions.transfer(to, amount).transact({'from': my_address})
```

**Трюк - симуляция перед отправкой:**
```python
# Проверяем что транзакция не упадет
try:
    contract.functions.transfer(to, amount).call({'from': my_address})
    print("Simulation OK, sending real transaction...")
    tx_hash = contract.functions.transfer(to, amount).transact({'from': my_address})
except Exception as e:
    print(f"Simulation failed: {e}")
```

---

## Question: Nonce в транзакции
**Difficulty**: Easy
**Type**: Text

Что такое nonce в транзакции? Зачем он нужен и что будет если использовать неправильный nonce?

**Answer**:

**Nonce** - порядковый номер транзакции от конкретного адреса, начинается с 0.

**Зачем нужен:**
1. **Защита от replay атак** - нельзя отправить транзакцию дважды
2. **Упорядочивание** - гарантирует последовательность выполнения
3. **Идентификация** - уникально идентифицирует транзакцию от адреса

**Как работает:**
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('...'))

# Получаем текущий nonce
address = '0x...'
nonce = w3.eth.get_transaction_count(address)

print(f"Next nonce: {nonce}")  # Например: 42

# Каждая новая транзакция увеличивает nonce
```

**Что будет если nonce неправильный:**

1. **Nonce слишком маленький** (уже использован)
   - Транзакция отклонена
   - Ошибка: "nonce too low" или "already known"

2. **Nonce слишком большой** (пропущен)
   - Транзакция "застрянет" в pending
   - Не будет выполнена пока не будут выполнены все предыдущие

3. **Правильный порядок:**
```
nonce 0: Executed ✅
nonce 1: Executed ✅
nonce 2: Pending...
nonce 3: STUCK! (ждет nonce 2)
```

**Проблема: параллельные транзакции**
```python
# WRONG - race condition!
tx1 = send_tx(nonce=w3.eth.get_transaction_count(address))
tx2 = send_tx(nonce=w3.eth.get_transaction_count(address))  # Тот же nonce!

# RIGHT - инкрементируем вручную
nonce = w3.eth.get_transaction_count(address)
tx1 = send_tx(nonce=nonce)
tx2 = send_tx(nonce=nonce + 1)
tx3 = send_tx(nonce=nonce + 2)
```

**Replace transaction (speed up):**
Можно "заменить" pending транзакцию отправив новую с тем же nonce но большим gas:
```python
# Оригинальная транзакция с низким gas
tx1 = send_tx(nonce=5, gasPrice=w3.to_wei(10, 'gwei'))

# Если застряла, отправляем с тем же nonce но выше gas
tx2 = send_tx(nonce=5, gasPrice=w3.to_wei(50, 'gwei'))  # Заменит tx1
```

---

## Question: Gas система
**Difficulty**: Medium
**Type**: Text

Объясни как работает gas в Ethereum: Gas Limit, Gas Price, Gas Used. Когда транзакция fails но gas все равно списывается?

**Answer**:

**3 ключевых понятия:**

**1. Gas Limit**
- Максимальное количество gas, которое ты готов потратить
- Устанавливается ДО выполнения
- Если операции требуют больше - транзакция reverts
- Неиспользованный gas возвращается

**2. Gas Price** (до EIP-1559)
- Цена за единицу gas в Gwei
- Чем выше - тем быстрее выполнится
- После EIP-1559: maxFeePerGas + maxPriorityFeePerGas

**3. Gas Used**
- Фактически потраченный gas
- Зависит от сложности операций
- Всегда ≤ Gas Limit

**Формула:**
```
Transaction Fee = Gas Used × Gas Price

Refund = (Gas Limit - Gas Used) × Gas Price
```

**Пример:**
```python
tx = {
    'gas': 100000,              # Gas Limit
    'gasPrice': w3.to_wei(50, 'gwei')
}

# Если использовано 21000 gas:
# Fee = 21000 × 50 = 1,050,000 Gwei = 0.00105 ETH
# Refund = (100000 - 21000) × 50 = 3,950,000 Gwei = 0.00395 ETH
```

**Почему gas списывается даже если транзакция fails:**

```solidity
function riskyOperation() public {
    // Тут уже потрачен gas на:
    // - Проверку подписи
    // - Загрузку кода
    // - Выполнение до этой строки
    
    require(someCondition, "Failed!");  // ❌ REVERT
    
    // State откатывается, но gas УЖЕ потрачен!
}
```

**Gas потрачен на:**
1. ✅ Валидацию транзакции
2. ✅ Загрузку кода контракта
3. ✅ Выполнение до require/revert
4. ❌ Изменения state (откатываются)

**В web3.py:**
```python
try:
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if tx_receipt.status == 0:
        print(f"Transaction FAILED!")
        print(f"But gas used: {tx_receipt.gasUsed}")  # Gas все равно списан!
    else:
        print(f"Success! Gas used: {tx_receipt.gasUsed}")
        
except Exception as e:
    print(f"Error: {e}")
```

**Оценка gas перед отправкой:**
```python
# Симуляция для оценки gas
estimated_gas = contract.functions.myFunction().estimate_gas({
    'from': my_address
})

print(f"Estimated: {estimated_gas}")

# Добавляем буфер 10-20%
tx = contract.functions.myFunction().build_transaction({
    'gas': int(estimated_gas * 1.2)
})
```

---

## Question: Получение NFT из кошелька
**Difficulty**: Hard
**Type**: Code

Клиент просит: "Построй backend API который возвращает все NFT в кошельке". Какой подход? Какие endpoints? Как получить NFT metadata?

**Answer**:

**Подход:**

1. **Опция А: Использовать Alchemy/Moralis API** (рекомендуется)
   - Готовые indexed данные
   - Быстро и надежно
   
2. **Опция Б: Парсить events вручную** (сложнее)
   - Больше контроля
   - Требует много ресурсов

**Решение с Alchemy:**

```python
from fastapi import FastAPI, HTTPException
from web3 import Web3
import requests

app = FastAPI()

ALCHEMY_KEY = "your_key"
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

@app.get("/api/nfts/{wallet_address}")
async def get_nfts(wallet_address: str):
    """Получить все NFT в кошельке"""
    
    # Alchemy getNFTs API
    url = f"{ALCHEMY_URL}/getNFTs/"
    params = {
        "owner": wallet_address,
        "withMetadata": "true"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching NFTs")
    
    data = response.json()
    
    # Форматируем результат
    nfts = []
    for nft in data.get('ownedNfts', []):
        nfts.append({
            "contract_address": nft['contract']['address'],
            "token_id": nft['id']['tokenId'],
            "name": nft.get('title', 'Unknown'),
            "description": nft.get('description', ''),
            "image": nft.get('media', [{}])[0].get('gateway', ''),
            "collection": nft['contract'].get('name', 'Unknown'),
            "balance": nft.get('balance', '1')
        })
    
    return {
        "wallet": wallet_address,
        "total_count": len(nfts),
        "nfts": nfts
    }

@app.get("/api/nft/{contract_address}/{token_id}")
async def get_nft_metadata(contract_address: str, token_id: int):
    """Получить metadata конкретного NFT"""
    
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    
    # ERC721 ABI для tokenURI
    erc721_abi = [
        {
            "inputs": [{"type": "uint256"}],
            "name": "tokenURI",
            "outputs": [{"type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=contract_address, abi=erc721_abi)
    
    try:
        # Получаем URI метаданных
        token_uri = contract.functions.tokenURI(token_id).call()
        
        # Если IPFS, конвертируем в gateway URL
        if token_uri.startswith('ipfs://'):
            token_uri = token_uri.replace('ipfs://', 'https://ipfs.io/ipfs/')
        
        # Загружаем метаданные
        metadata_response = requests.get(token_uri)
        metadata = metadata_response.json()
        
        return {
            "contract": contract_address,
            "token_id": token_id,
            "token_uri": token_uri,
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Вариант БЕЗ Alchemy (только web3.py):**

```python
from web3 import Web3

def get_nfts_manual(wallet_address: str, contract_address: str):
    """Получить NFT из конкретной коллекции (требует индексацию events)"""
    
    w3 = Web3(Web3.HTTPProvider('...'))
    
    # ERC721 ABI
    erc721_abi = [...]
    contract = w3.eth.contract(address=contract_address, abi=erc721_abi)
    
    # Получаем Transfer events для этого адреса
    transfer_filter = contract.events.Transfer.create_filter(
        fromBlock=0,
        argument_filters={'to': wallet_address}
    )
    
    # Собираем token IDs
    owned_tokens = set()
    
    for event in transfer_filter.get_all_entries():
        token_id = event.args['tokenId']
        
        # Проверяем что токен все еще у этого владельца
        current_owner = contract.functions.ownerOf(token_id).call()
        if current_owner.lower() == wallet_address.lower():
            owned_tokens.add(token_id)
    
    return list(owned_tokens)
```

**Полная структура API:**

```
GET /api/nfts/{wallet_address}           # Все NFT в кошельке
GET /api/nft/{contract}/{token_id}       # Конкретный NFT
GET /api/collections                     # Популярные коллекции
GET /api/collection/{contract}/nfts      # Все NFT из коллекции
```

