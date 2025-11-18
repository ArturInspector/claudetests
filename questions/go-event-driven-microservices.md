# Topic: Go Event-Driven Architecture & Microservices

## Question: Что такое Event-Driven Architecture?
**Difficulty**: Easy
**Type**: Text

Объясни простыми словами, что такое Event-Driven Architecture (EDA) и в чем её отличие от традиционного request-response подхода.

**Answer**:

**Event-Driven Architecture** - это архитектурный паттерн, где компоненты системы взаимодействуют через события (events), а не через прямые вызовы.

**Основные отличия:**

1. **Request-Response (синхронный):**
   - Сервис A вызывает сервис B и ждет ответа
   - Блокирующее взаимодействие
   - Тесная связанность

2. **Event-Driven (асинхронный):**
   - Сервис A публикует событие "OrderCreated"
   - Сервис B подписывается и реагирует на это событие
   - Неблокирующее взаимодействие
   - Слабая связанность

**Пример:**
```
Пользователь создает заказ → OrderService публикует событие "OrderCreated"
  ↓
PaymentService получает событие → обрабатывает платеж → публикует "PaymentProcessed"
  ↓
ShippingService получает событие → создает доставку
```

**Преимущества:**
- Масштабируемость (можно добавить новые подписчики)
- Отказоустойчивость (если один сервис упал, другие продолжают работать)
- Гибкость (легко добавлять новые обработчики)

---

## Question: Event Bus в Go
**Difficulty**: Medium
**Type**: Code

Как реализовать простой Event Bus в Go для микросервисов? Напиши базовую структуру.

**Answer**:

```go
package main

import (
    "sync"
    "reflect"
)

// EventBus - простой event bus
type EventBus struct {
    subscribers map[string][]chan interface{}
    mutex       sync.RWMutex
}

// NewEventBus создает новый EventBus
func NewEventBus() *EventBus {
    return &EventBus{
        subscribers: make(map[string][]chan interface{}),
    }
}

// Subscribe подписывается на событие
func (eb *EventBus) Subscribe(eventType string) <-chan interface{} {
    eb.mutex.Lock()
    defer eb.mutex.Unlock()
    
    ch := make(chan interface{}, 1)
    eb.subscribers[eventType] = append(eb.subscribers[eventType], ch)
    
    return ch
}

// Publish публикует событие
func (eb *EventBus) Publish(eventType string, data interface{}) {
    eb.mutex.RLock()
    defer eb.mutex.RUnlock()
    
    for _, ch := range eb.subscribers[eventType] {
        select {
        case ch <- data:
        default:
            // Канал полон, пропускаем (non-blocking)
        }
    }
}

// Пример использования:
type OrderCreatedEvent struct {
    OrderID   int
    UserID    int
    Amount    float64
    Timestamp int64
}

func main() {
    bus := NewEventBus()
    
    // Подписчик 1: Payment Service
    paymentCh := bus.Subscribe("OrderCreated")
    go func() {
        for event := range paymentCh {
            order := event.(OrderCreatedEvent)
            fmt.Printf("Processing payment for order %d\n", order.OrderID)
        }
    }()
    
    // Подписчик 2: Notification Service
    notifyCh := bus.Subscribe("OrderCreated")
    go func() {
        for event := range notifyCh {
            order := event.(OrderCreatedEvent)
            fmt.Printf("Sending notification for order %d\n", order.OrderID)
        }
    }()
    
    // Публикация события
    bus.Publish("OrderCreated", OrderCreatedEvent{
        OrderID:   123,
        UserID:    456,
        Amount:    99.99,
        Timestamp: time.Now().Unix(),
    })
}
```

**Для production лучше использовать готовые решения:**
- **NATS** - легковесный message broker
- **RabbitMQ** - надежный message broker
- **Apache Kafka** - для больших объемов данных

---

## Question: Обработка Ethereum Events в Go
**Difficulty**: Medium
**Type**: Code

Как в Go микросервисе подписаться на события из смарт-контракта Ethereum и обработать их?

**Answer**:

```go
package main

import (
    "context"
    "fmt"
    "log"
    "math/big"
    
    "github.com/ethereum/go-ethereum"
    "github.com/ethereum/go-ethereum/accounts/abi"
    "github.com/ethereum/go-ethereum/common"
    "github.com/ethereum/go-ethereum/core/types"
    "github.com/ethereum/go-ethereum/ethclient"
)

// Event структура для Transfer события ERC-20
type TransferEvent struct {
    From    common.Address
    To      common.Address
    Value   *big.Int
    BlockNumber uint64
    TxHash  common.Hash
}

// EventListener слушает события из контракта
type EventListener struct {
    client     *ethclient.Client
    contractAddr common.Address
    contractABI   abi.ABI
}

func NewEventListener(rpcURL string, contractAddress string) (*EventListener, error) {
    client, err := ethclient.Dial(rpcURL)
    if err != nil {
        return nil, err
    }
    
    // ABI для Transfer события (из ERC-20)
    contractABI, err := abi.JSON(strings.NewReader(`[{
        "anonymous": false,
        "inputs": [
            {"indexed": true, "name": "from", "type": "address"},
            {"indexed": true, "name": "to", "type": "address"},
            {"indexed": false, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }]`))
    if err != nil {
        return nil, err
    }
    
    return &EventListener{
        client:       client,
        contractAddr: common.HexToAddress(contractAddress),
        contractABI:  contractABI,
    }, nil
}

// ListenToTransferEvents слушает Transfer события
func (el *EventListener) ListenToTransferEvents(ctx context.Context, eventCh chan<- TransferEvent) error {
    // Создаем query для фильтрации событий
    query := ethereum.FilterQuery{
        Addresses: []common.Address{el.contractAddr},
        Topics: [][]common.Hash{
            {el.contractABI.Events["Transfer"].ID}, // Только Transfer события
        },
    }
    
    logs := make(chan types.Log)
    sub, err := el.client.SubscribeFilterLogs(ctx, query, logs)
    if err != nil {
        return err
    }
    
    go func() {
        for {
            select {
            case err := <-sub.Err():
                log.Printf("Subscription error: %v", err)
                return
            case logEntry := <-logs:
                // Парсим событие
                event := TransferEvent{}
                
                err := el.contractABI.UnpackIntoInterface(&event, "Transfer", logEntry.Data)
                if err != nil {
                    log.Printf("Error unpacking event: %v", err)
                    continue
                }
                
                // Извлекаем indexed параметры
                event.From = common.BytesToAddress(logEntry.Topics[1].Bytes())
                event.To = common.BytesToAddress(logEntry.Topics[2].Bytes())
                event.BlockNumber = logEntry.BlockNumber
                event.TxHash = logEntry.TxHash
                
                eventCh <- event
            case <-ctx.Done():
                return
            }
        }
    }()
    
    return nil
}

// Пример использования:
func main() {
    listener, err := NewEventListener(
        "wss://mainnet.infura.io/ws/v3/YOUR_KEY",
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC контракт
    )
    if err != nil {
        log.Fatal(err)
    }
    
    eventCh := make(chan TransferEvent, 10)
    
    ctx := context.Background()
    go listener.ListenToTransferEvents(ctx, eventCh)
    
    // Обработка событий
    for event := range eventCh {
        fmt.Printf("Transfer: %s -> %s, Amount: %s\n", 
            event.From.Hex(), 
            event.To.Hex(), 
            event.Value.String())
        
        // Здесь можно отправить событие в Event Bus для других микросервисов
        // bus.Publish("TokenTransfer", event)
    }
}
```

**Важные моменты:**
- Используй **WebSocket** для real-time событий (не HTTP polling)
- Обрабатывай ошибки подписки
- Используй контекст для graceful shutdown
- События можно публиковать в Event Bus для других сервисов

---

## Question: Pub/Sub паттерн в микросервисах
**Difficulty**: Medium
**Type**: Text

Объясни паттерн Pub/Sub (Publisher/Subscriber) и как он используется в микросервисной архитектуре. В чем разница с обычным Event Bus?

**Answer**:

**Pub/Sub (Publisher/Subscriber)** - это паттерн, где отправители (publishers) публикуют сообщения в канал, не зная кто их получит, а получатели (subscribers) подписываются на интересующие их каналы.

**Основные компоненты:**

1. **Publisher** - публикует события в канал
2. **Subscriber** - подписывается на канал и получает события
3. **Message Broker** - промежуточный слой (NATS, RabbitMQ, Kafka)

**Отличия от простого Event Bus:**

| Event Bus | Pub/Sub |
|-----------|---------|
| В памяти приложения | Внешний message broker |
| События теряются при перезапуске | Сообщения персистентны |
| Один процесс | Распределенная система |
| Нет гарантий доставки | Гарантии доставки (at-least-once, exactly-once) |

**Пример архитектуры:**

```
┌─────────────┐
│ OrderService│ ──publish──> [NATS/Kafka] <──subscribe── ┌──────────────┐
│             │   "OrderCreated"                         │PaymentService│
└─────────────┘                                          └──────────────┘
                                                              │
                                                              │
┌─────────────┐                                              │
│UserService  │ <──subscribe── [NATS/Kafka] <──publish───────┘
└─────────────┘   "PaymentProcessed"
```

**Преимущества Pub/Sub:**
- **Decoupling** - сервисы не знают друг о друге
- **Scalability** - можно добавить много подписчиков
- **Reliability** - сообщения не теряются
- **Flexibility** - легко добавлять новые сервисы

**Пример с NATS в Go:**

```go
// Publisher
nc, _ := nats.Connect("nats://localhost:4222")
nc.Publish("orders.created", []byte(`{"orderId": 123}`))

// Subscriber
nc.Subscribe("orders.created", func(msg *nats.Msg) {
    fmt.Printf("Received: %s\n", string(msg.Data))
})
```

---

## Question: Event Sourcing в Go
**Difficulty**: Hard
**Type**: Text

Что такое Event Sourcing и как его можно применить в Go микросервисе? Приведи пример.

**Answer**:

**Event Sourcing** - это паттерн, где состояние приложения хранится как последовательность событий, а не как текущий snapshot данных.

**Основная идея:**
- Вместо обновления записи в БД, сохраняем событие "OrderCreated", "OrderPaid", "OrderShipped"
- Текущее состояние = сумма всех событий
- Можно "перемотать" время и посмотреть состояние на любой момент

**Пример структуры:**

```go
// Event интерфейс
type Event interface {
    EventType() string
    AggregateID() string
    Timestamp() time.Time
}

// События
type OrderCreatedEvent struct {
    OrderID   string
    UserID    string
    Amount    float64
    CreatedAt time.Time
}

func (e OrderCreatedEvent) EventType() string { return "OrderCreated" }
func (e OrderCreatedEvent) AggregateID() string { return e.OrderID }
func (e OrderCreatedEvent) Timestamp() time.Time { return e.CreatedAt }

type OrderPaidEvent struct {
    OrderID   string
    PaymentID string
    PaidAt    time.Time
}

// Event Store - хранилище событий
type EventStore interface {
    Save(aggregateID string, events []Event) error
    Load(aggregateID string) ([]Event, error)
}

// Order Aggregate - восстанавливает состояние из событий
type Order struct {
    ID      string
    UserID  string
    Amount  float64
    Status  string // "created", "paid", "shipped"
}

func NewOrderFromEvents(events []Event) *Order {
    order := &Order{}
    
    for _, event := range events {
        switch e := event.(type) {
        case OrderCreatedEvent:
            order.ID = e.OrderID
            order.UserID = e.UserID
            order.Amount = e.Amount
            order.Status = "created"
            
        case OrderPaidEvent:
            order.Status = "paid"
            
        case OrderShippedEvent:
            order.Status = "shipped"
        }
    }
    
    return order
}

// Сохранение события
func (es *InMemoryEventStore) Save(aggregateID string, events []Event) error {
    for _, event := range events {
        es.events[aggregateID] = append(es.events[aggregateID], event)
    }
    return nil
}
```

**Преимущества:**
- **Audit trail** - полная история изменений
- **Time travel** - можно посмотреть состояние на любой момент
- **Debugging** - легко понять что произошло
- **Scalability** - события можно обрабатывать асинхронно

**Недостатки:**
- Сложнее реализация
- Нужно проектировать события заранее
- Может быть медленнее для чтения (нужно пересчитать состояние)

---

## Question: Обработка ошибок в Event-Driven системах
**Difficulty**: Medium
**Type**: Text

Как правильно обрабатывать ошибки в event-driven архитектуре? Что делать, если обработчик события упал?

**Answer**:

В event-driven системах ошибки критичны, так как события могут быть потеряны. Вот основные стратегии:

**1. Retry механизм:**

```go
type EventHandler struct {
    maxRetries int
    retryDelay time.Duration
}

func (h *EventHandler) HandleWithRetry(event Event) error {
    for i := 0; i < h.maxRetries; i++ {
        err := h.handle(event)
        if err == nil {
            return nil
        }
        
        log.Printf("Attempt %d failed: %v", i+1, err)
        time.Sleep(h.retryDelay)
    }
    
    return fmt.Errorf("failed after %d retries", h.maxRetries)
}
```

**2. Dead Letter Queue (DLQ):**

Если событие не удалось обработать после N попыток, отправляем его в DLQ для ручного разбора:

```go
type DeadLetterQueue struct {
    failedEvents []FailedEvent
}

type FailedEvent struct {
    Event     Event
    Error     error
    Timestamp time.Time
    Retries   int
}

func (dlq *DeadLetterQueue) AddFailedEvent(event Event, err error) {
    dlq.failedEvents = append(dlq.failedEvents, FailedEvent{
        Event:     event,
        Error:     err,
        Timestamp: time.Now(),
    })
    // Можно отправить алерт администратору
}
```

**3. Idempotency (идемпотентность):**

Обработчик должен быть идемпотентным - повторная обработка того же события не должна менять результат:

```go
func (h *EventHandler) HandleOrderCreated(event OrderCreatedEvent) error {
    // Проверяем, не обработали ли мы уже это событие
    if h.isProcessed(event.OrderID) {
        log.Printf("Event %s already processed, skipping", event.OrderID)
        return nil
    }
    
    // Обработка...
    h.markAsProcessed(event.OrderID)
    return nil
}
```

**4. Circuit Breaker:**

Если сервис постоянно падает, временно прекращаем отправку ему событий:

```go
type CircuitBreaker struct {
    failures    int
    threshold   int
    timeout     time.Duration
    lastFailure time.Time
    state       string // "closed", "open", "half-open"
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    if cb.state == "open" {
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.state = "half-open" // Пробуем снова
        } else {
            return errors.New("circuit breaker is open")
        }
    }
    
    err := fn()
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.threshold {
            cb.state = "open"
        }
        return err
    }
    
    cb.failures = 0
    cb.state = "closed"
    return nil
}
```

**5. Event Versioning:**

При изменении структуры события используй версионирование:

```go
type EventV1 struct {
    OrderID string
    Amount  float64
}

type EventV2 struct {
    OrderID    string
    Amount     float64
    Currency   string // Новое поле
    Version    int    // Версия события
}
```

**Best Practices:**
- Всегда логируй ошибки
- Используй мониторинг (Prometheus, Grafana)
- Настрой алерты на критичные ошибки
- Тестируй обработку ошибок

---

## Question: Синхронная vs Асинхронная коммуникация
**Difficulty**: Easy
**Type**: Text

В чем разница между синхронной и асинхронной коммуникацией в микросервисах? Когда использовать каждую?

**Answer**:

**Синхронная коммуникация:**
- Сервис A вызывает сервис B и **ждет** ответа
- Блокирующее взаимодействие
- Пример: HTTP REST API, gRPC

```
User → OrderService → PaymentService (ждет ответа) → ShippingService (ждет ответа)
```

**Асинхронная коммуникация:**
- Сервис A отправляет сообщение и **не ждет** ответа
- Неблокирующее взаимодействие
- Пример: Message Queue, Event Bus

```
User → OrderService → [Queue] → PaymentService (обрабатывает когда может)
                      ↓
                   ShippingService (тоже обрабатывает)
```

**Сравнение:**

| Критерий | Синхронная | Асинхронная |
|----------|------------|-------------|
| **Скорость ответа** | Быстро (если все работает) | Медленнее (но не блокирует) |
| **Отказоустойчивость** | Плохая (один сервис упал = все упало) | Хорошая (события в очереди) |
| **Сложность** | Проще | Сложнее (нужен message broker) |
| **Debugging** | Проще (видно весь flow) | Сложнее (события где-то в очереди) |
| **Масштабируемость** | Ограничена | Отличная |

**Когда использовать синхронную:**
- Нужен немедленный ответ (проверка баланса)
- Простые операции (CRUD)
- Когда отказ одного сервиса должен остановить операцию

**Когда использовать асинхронную:**
- Долгие операции (отправка email, генерация отчетов)
- Когда можно обработать позже (уведомления)
- Высокая нагрузка (события можно обработать в фоне)
- Когда нужна отказоустойчивость

**Пример гибридного подхода:**

```go
// Синхронно: проверяем баланс
balance, err := paymentService.CheckBalance(userID)
if err != nil || balance < amount {
    return err
}

// Асинхронно: отправляем уведомление
eventBus.Publish("OrderCreated", OrderCreatedEvent{
    OrderID: orderID,
    UserID:  userID,
})
// Не ждем ответа, продолжаем работу
```

---

## Question: On-Chain Events как источник событий
**Difficulty**: Medium
**Type**: Text

Как использовать события из блокчейна (on-chain events) как источник событий для микросервисов? Какие есть паттерны?

**Answer**:

Блокчейн события (например, Ethereum Events) можно использовать как источник событий для микросервисов. Это называется **Blockchain Event Sourcing**.

**Архитектура:**

```
┌─────────────┐
│ Ethereum    │ ──Events──> ┌──────────────┐ ──Process──> ┌─────────────┐
│ Smart       │             │Event Listener│              │Microservice │
│ Contract    │             │   Service    │              │   (Go)      │
└─────────────┘             └──────────────┘              └─────────────┘
                                      │
                                      ↓
                              ┌──────────────┐
                              │  Event Bus   │
                              │  (NATS/Kafka)│
                              └──────────────┘
```

**Паттерны:**

**1. Event Listener Service (отдельный сервис):**

```go
// Слушаем события из контракта
func (s *EventListenerService) Listen() {
    logs := make(chan types.Log)
    sub, _ := s.client.SubscribeFilterLogs(ctx, query, logs)
    
    for log := range logs {
        event := parseEvent(log)
        
        // Публикуем в Event Bus для других сервисов
        s.eventBus.Publish("TokenTransfer", event)
    }
}
```

**2. Event Replay (воспроизведение событий):**

Если сервис упал, можно перечитать события с определенного блока:

```go
func (s *Service) ReplayEvents(fromBlock uint64) {
    // Читаем все события с блока fromBlock до текущего
    for block := fromBlock; block <= currentBlock; block++ {
        events := s.getEventsAtBlock(block)
        for _, event := range events {
            s.processEvent(event)
        }
    }
}
```

**3. Event Filtering (фильтрация):**

Подписываемся только на нужные события:

```go
// Только Transfer события для определенного токена
query := ethereum.FilterQuery{
    Addresses: []common.Address{tokenAddress},
    Topics: [][]common.Hash{
        {transferEventID},
        {nil, userAddress.Hash()}, // Только от/к этому адресу
    },
}
```

**4. Event Aggregation (агрегация):**

Собираем несколько событий в одно:

```go
// Слушаем Transfer события и агрегируем по пользователю
type UserBalance struct {
    UserID  string
    Balance *big.Int
    Events  []TransferEvent
}

func (s *Service) AggregateTransfers(userID string) UserBalance {
    // Собираем все Transfer события для пользователя
    events := s.getUserTransferEvents(userID)
    
    balance := big.NewInt(0)
    for _, event := range events {
        if event.To == userID {
            balance.Add(balance, event.Value)
        } else {
            balance.Sub(balance, event.Value)
        }
    }
    
    return UserBalance{
        UserID:  userID,
        Balance: balance,
        Events:  events,
    }
}
```

**Преимущества:**
- **Immutable источник** - события в блокчейне нельзя изменить
- **Прозрачность** - все события публичны
- **Аудит** - полная история операций
- **Decoupling** - микросервисы не зависят напрямую от блокчейна

**Недостатки:**
- **Latency** - события появляются только после подтверждения блока
- **Cost** - нужно платить за gas при записи событий
- **Сложность** - нужно обрабатывать реорганизации блоков

**Best Practices:**
- Используй WebSocket для real-time событий
- Обрабатывай реорганизации блоков (chain reorgs)
- Храни последний обработанный блок
- Используй idempotency для обработки событий

---

## Question: Graceful Shutdown в Event-Driven сервисе
**Difficulty**: Medium
**Type**: Code

Как правильно реализовать graceful shutdown для Go сервиса, который слушает события? Напиши пример.

**Answer**:

Graceful shutdown важен для event-driven сервисов, чтобы не потерять события при остановке.

```go
package main

import (
    "context"
    "fmt"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

type EventService struct {
    eventCh     chan Event
    subscribers []chan Event
    wg          sync.WaitGroup
    ctx         context.Context
    cancel      context.CancelFunc
}

func NewEventService() *EventService {
    ctx, cancel := context.WithCancel(context.Background())
    return &EventService{
        eventCh:     make(chan Event, 100),
        subscribers: make([]chan Event, 0),
        ctx:         ctx,
        cancel:      cancel,
    }
}

// Start запускает сервис
func (s *EventService) Start() {
    // Запускаем обработчик событий
    s.wg.Add(1)
    go s.eventProcessor()
    
    // Запускаем подписчиков
    for i := range s.subscribers {
        s.wg.Add(1)
        go s.subscriber(s.subscribers[i])
    }
}

// Stop останавливает сервис gracefully
func (s *EventService) Stop() error {
    fmt.Println("Shutting down...")
    
    // Отменяем контекст (сигнал всем горутинам остановиться)
    s.cancel()
    
    // Закрываем канал событий (больше не принимаем новые)
    close(s.eventCh)
    
    // Ждем завершения всех горутин (с таймаутом)
    done := make(chan struct{})
    go func() {
        s.wg.Wait()
        close(done)
    }()
    
    select {
    case <-done:
        fmt.Println("All goroutines stopped")
        return nil
    case <-time.After(10 * time.Second):
        return fmt.Errorf("shutdown timeout: some goroutines didn't stop")
    }
}

// eventProcessor обрабатывает события
func (s *EventService) eventProcessor() {
    defer s.wg.Done()
    
    for {
        select {
        case event, ok := <-s.eventCh:
            if !ok {
                // Канал закрыт, обрабатываем оставшиеся события
                fmt.Println("Event channel closed, processing remaining events...")
                return
            }
            s.processEvent(event)
            
        case <-s.ctx.Done():
            // Контекст отменен, останавливаемся
            fmt.Println("Context cancelled, stopping processor...")
            return
        }
    }
}

// subscriber обрабатывает события для подписчика
func (s *EventService) subscriber(ch chan Event) {
    defer s.wg.Done()
    
    for {
        select {
        case event, ok := <-ch:
            if !ok {
                return
            }
            s.handleEvent(event)
            
        case <-s.ctx.Done():
            // Обрабатываем оставшиеся события перед выходом
            for {
                select {
                case event := <-ch:
                    s.handleEvent(event)
                default:
                    return
                }
            }
        }
    }
}

func (s *EventService) processEvent(event Event) {
    // Распределяем событие всем подписчикам
    for _, ch := range s.subscribers {
        select {
        case ch <- event:
        default:
            // Канал полон, логируем но не блокируем
            fmt.Printf("Subscriber channel full, skipping event\n")
        }
    }
}

func (s *EventService) handleEvent(event Event) {
    fmt.Printf("Handling event: %+v\n", event)
    // Обработка события...
}

// main с обработкой сигналов
func main() {
    service := NewEventService()
    service.Start()
    
    // Обработка сигналов для graceful shutdown
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    
    // Ждем сигнал остановки
    <-sigCh
    fmt.Println("\nReceived shutdown signal")
    
    // Graceful shutdown
    if err := service.Stop(); err != nil {
        fmt.Printf("Error during shutdown: %v\n", err)
        os.Exit(1)
    }
    
    fmt.Println("Service stopped successfully")
}
```

**Ключевые моменты:**

1. **Context для отмены** - все горутины слушают `ctx.Done()`
2. **Закрытие каналов** - закрываем каналы, чтобы горутины знали что остановиться
3. **WaitGroup** - ждем завершения всех горутин
4. **Таймаут** - если горутины не остановились за 10 секунд, форсируем остановку
5. **Обработка сигналов** - ловим SIGINT/SIGTERM для graceful shutdown

**Для production добавь:**
- Health checks endpoint
- Метрики (Prometheus)
- Логирование
- Сохранение состояния перед остановкой

