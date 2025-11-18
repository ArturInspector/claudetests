# Topic: Architecture Patterns

## Concept: Clean Architecture и Layered Architecture
**Tags**: architecture, clean-code, separation-of-concerns, dependency-inversion
**Estimated Time**: 30 minutes

### Level 1: Что такое Clean Architecture?
Объясни основные принципы Clean Architecture и зачем она нужна.

**Answer**:
Clean Architecture (предложена Робертом Мартином) - это подход к организации кода, где зависимости направлены внутрь, к бизнес-логике. Внешние детали (БД, UI, фреймворки) зависят от внутренних слоев, а не наоборот.

Основные слои (от внешнего к внутреннему):
1. **Frameworks & Drivers** - UI, веб-фреймворки, БД, внешние API
2. **Interface Adapters** - контроллеры, презентеры, шлюзы
3. **Use Cases** - бизнес-логика приложения
4. **Entities** - бизнес-сущности и правила

Принцип: **Dependency Rule** - зависимости направлены только внутрь. Внутренние слои не знают о внешних.

Пример структуры:
```
src/
  domain/          # Entities - бизнес-логика
    user.py
    order.py
  use_cases/       # Use Cases - сценарии использования
    create_user.py
    process_order.py
  interfaces/      # Interface Adapters
    controllers/
    repositories/
  infrastructure/  # Frameworks & Drivers
    database/
    api/
```

**Почему это важно**: Изменения в БД или UI не требуют изменения бизнес-логики. Тестирование упрощается - можно мокировать внешние зависимости.

### Level 2: Как реализовать Dependency Inversion в Python?
Покажи практический пример Dependency Inversion Principle в Python с репозиториями и use cases.

**Answer**:
Dependency Inversion Principle (DIP) - высокоуровневые модули не должны зависеть от низкоуровневых. Оба должны зависеть от абстракций.

Пример без DIP (плохо):
```python
# Плохо: Use Case зависит от конкретной реализации БД
class CreateUserUseCase:
    def __init__(self):
        self.db = PostgreSQLDatabase()  # Жесткая зависимость
    
    def execute(self, user_data):
        # Бизнес-логика смешана с деталями БД
        self.db.execute("INSERT INTO users...")
```

Пример с DIP (хорошо):
```python
# 1. Абстракция (интерфейс)
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        pass

# 2. Use Case зависит от абстракции
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo  # Зависимость от абстракции
    
    def execute(self, email: str, name: str) -> User:
        # Чистая бизнес-логика
        if self.user_repo.find_by_email(email):
            raise ValueError("User already exists")
        
        user = User(email=email, name=name)
        return self.user_repo.save(user)

# 3. Конкретная реализация
class PostgreSQLUserRepository(UserRepository):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, user: User) -> User:
        # Детали работы с PostgreSQL
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO users...")
        return user
    
    def find_by_email(self, email: str) -> User | None:
        # Детали работы с PostgreSQL
        pass

# 4. Использование с dependency injection
repo = PostgreSQLUserRepository(db_connection)
use_case = CreateUserUseCase(repo)
user = use_case.execute("test@example.com", "Test User")
```

**Преимущества**:
- Можно заменить PostgreSQL на MongoDB без изменения Use Case
- Легко тестировать - мокируем `UserRepository`
- Бизнес-логика не знает о деталях хранения

### Level 3: Как организовать Domain-Driven Design (DDD) в Python?
Объясни как применить DDD паттерны: Entities, Value Objects, Aggregates, Domain Services.

**Answer**:
DDD фокусируется на моделировании бизнес-домена. Основные строительные блоки:

**1. Entity** - объект с уникальной идентичностью:
```python
class User:
    def __init__(self, user_id: str, email: str, name: str):
        self.id = user_id  # Идентификатор
        self.email = email
        self.name = name
        self._balance = Money(0)  # Value Object
    
    def change_email(self, new_email: str):
        if not self._is_valid_email(new_email):
            raise ValueError("Invalid email")
        self.email = new_email
    
    def _is_valid_email(self, email: str) -> bool:
        # Бизнес-правило валидации
        return "@" in email and "." in email.split("@")[1]
```

**2. Value Object** - объект без идентичности, определяется значениями:
```python
class Money:
    def __init__(self, amount: Decimal, currency: str = "USD"):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.amount = amount
        self.currency = currency
    
    def __eq__(self, other):
        return (self.amount == other.amount and 
                self.currency == other.currency)
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

**3. Aggregate** - кластер связанных объектов с единой точкой доступа (Aggregate Root):
```python
class Order:  # Aggregate Root
    def __init__(self, order_id: str, customer: User):
        self.id = order_id
        self.customer = customer
        self._items: list[OrderItem] = []
        self.status = OrderStatus.PENDING
        self.total = Money(0)
    
    def add_item(self, product: Product, quantity: int):
        # Бизнес-правило: нельзя добавлять в завершенный заказ
        if self.status == OrderStatus.COMPLETED:
            raise ValueError("Cannot modify completed order")
        
        item = OrderItem(product, quantity)
        self._items.append(item)
        self._recalculate_total()
    
    def _recalculate_total(self):
        self.total = Money(0)
        for item in self._items:
            self.total = self.total.add(item.subtotal)
    
    def complete(self):
        if self.total.amount == 0:
            raise ValueError("Cannot complete empty order")
        self.status = OrderStatus.COMPLETED
```

**4. Domain Service** - операция, не принадлежащая одному Entity:
```python
class TransferService:  # Domain Service
    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo
    
    def transfer(self, from_account_id: str, to_account_id: str, amount: Money):
        from_account = self.account_repo.find_by_id(from_account_id)
        to_account = self.account_repo.find_by_id(to_account_id)
        
        # Бизнес-правило: проверка лимитов
        if from_account.balance.amount < amount.amount:
            raise ValueError("Insufficient funds")
        
        # Бизнес-правило: нельзя переводить самому себе
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to same account")
        
        from_account.withdraw(amount)
        to_account.deposit(amount)
        
        self.account_repo.save(from_account)
        self.account_repo.save(to_account)
```

**Ключевые принципы DDD**:
- Ubiquitous Language - один язык для разработчиков и бизнеса
- Bounded Context - четкие границы доменов
- Aggregate Root контролирует доступ к внутренним объектам

### Level 4: Как масштабировать Clean Architecture для больших проектов?
Объясни как организовать модульную архитектуру с Bounded Contexts, Event-Driven коммуникацией и CQRS.

**Answer**:
Для больших систем нужна модульная архитектура с четкими границами.

**1. Модульная структура с Bounded Contexts**:
```
src/
  modules/
    users/
      domain/
        entities/
        value_objects/
        services/
      application/
        use_cases/
        dto/
      infrastructure/
        repositories/
        external_services/
      interfaces/
        api/
        cli/
    
    orders/
      domain/
      application/
      infrastructure/
      interfaces/
    
    payments/
      domain/
      application/
      infrastructure/
      interfaces/
```

Каждый модуль - независимый Bounded Context со своими правилами.

**2. Event-Driven коммуникация между модулями**:
```python
# Domain Event
class UserCreatedEvent:
    def __init__(self, user_id: str, email: str, timestamp: datetime):
        self.user_id = user_id
        self.email = email
        self.timestamp = timestamp

# Event Publisher (в модуле Users)
class UserService:
    def __init__(self, user_repo: UserRepository, event_bus: EventBus):
        self.user_repo = user_repo
        self.event_bus = event_bus
    
    def create_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        self.user_repo.save(user)
        
        # Публикуем событие
        event = UserCreatedEvent(user.id, email, datetime.now())
        self.event_bus.publish(event)
        
        return user

# Event Handler (в модуле Orders)
class CreateCartOnUserCreated:
    def __init__(self, cart_repo: CartRepository):
        self.cart_repo = cart_repo
    
    def handle(self, event: UserCreatedEvent):
        # Автоматически создаем корзину для нового пользователя
        cart = Cart(user_id=event.user_id)
        self.cart_repo.save(cart)
```

**3. CQRS (Command Query Responsibility Segregation)**:
Разделение операций чтения и записи:

```python
# Command Side (Write Model)
class CreateOrderCommand:
    def __init__(self, user_id: str, items: list[OrderItemDTO]):
        self.user_id = user_id
        self.items = items

class CreateOrderHandler:
    def __init__(self, order_repo: OrderRepository, event_bus: EventBus):
        self.order_repo = order_repo
        self.event_bus = event_bus
    
    def handle(self, command: CreateOrderCommand) -> str:
        order = Order(user_id=command.user_id)
        for item in command.items:
            order.add_item(item.product_id, item.quantity)
        
        self.order_repo.save(order)
        self.event_bus.publish(OrderCreatedEvent(order.id))
        return order.id

# Query Side (Read Model) - оптимизирован для чтения
class OrderReadModel:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user_orders(self, user_id: str) -> list[dict]:
        # Денормализованная таблица для быстрого чтения
        query = """
            SELECT o.id, o.total, o.status, o.created_at,
                   json_agg(json_build_object('name', p.name, 'quantity', oi.quantity)) as items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s
            GROUP BY o.id
        """
        return self.db.fetch_all(query, [user_id])
```

**4. Hexagonal Architecture (Ports & Adapters)**:
```python
# Port (интерфейс)
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: Money, card_token: str) -> PaymentResult:
        pass

# Adapter (реализация)
class StripePaymentGateway(PaymentGateway):
    def __init__(self, api_key: str):
        self.stripe = stripe.Client(api_key)
    
    def charge(self, amount: Money, card_token: str) -> PaymentResult:
        # Адаптация к внешнему API
        charge = self.stripe.charges.create(
            amount=int(amount.amount * 100),  # Конвертация в центы
            currency=amount.currency.lower(),
            source=card_token
        )
        return PaymentResult(success=charge.status == "succeeded")

# Use Case использует Port, не знает об Adapter
class ProcessPaymentUseCase:
    def __init__(self, payment_gateway: PaymentGateway):
        self.payment_gateway = payment_gateway  # Зависит от Port
    
    def execute(self, order_id: str, card_token: str):
        order = self.order_repo.find_by_id(order_id)
        result = self.payment_gateway.charge(order.total, card_token)
        # ...
```

**Преимущества такой архитектуры**:
- Модули независимы - можно разрабатывать параллельно
- Легко тестировать - мокируем порты
- Масштабируемо - каждый модуль может иметь свою БД
- Гибкость - можно заменить Stripe на PayPal без изменения Use Cases

**Resources**:
- [Article] https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html - Clean Architecture by Robert Martin
- [Book] Domain-Driven Design by Eric Evans - DDD классика
- [Article] https://martinfowler.com/bliki/HexagonalArchitecture.html - Hexagonal Architecture
- [Code] https://github.com/cosmic-python/code - Примеры из книги "Architecture Patterns with Python"
- [Video] https://www.youtube.com/watch?v=CnailTcJV_U - Clean Architecture в Python

**Related Concepts**: SOLID Principles, Dependency Injection, Repository Pattern, Event Sourcing, Microservices

---

## Concept: CQRS и Event Sourcing
**Tags**: cqrs, event-sourcing, scalability, read-write-separation
**Estimated Time**: 35 minutes

### Level 1: Что такое CQRS и зачем он нужен?
Объясни концепцию Command Query Responsibility Segregation и когда его использовать.

**Answer**:
CQRS (Command Query Responsibility Segregation) - разделение моделей для чтения (Query) и записи (Command). Вместо одной модели для обеих операций используются разные оптимизированные модели.

**Проблема традиционного подхода**:
```python
# Одна модель для всего
class Order:
    def __init__(self, id, user_id, items, status):
        self.id = id
        self.user_id = user_id
        self.items = items  # Сложные объекты для записи
        self.status = status
    
    def save(self):
        # Сложная логика сохранения
        pass
    
    def get_user_orders(self, user_id):
        # Медленный запрос с JOIN'ами
        pass
```

**Решение с CQRS**:
```python
# Command Model (Write) - оптимизирован для записи
class OrderAggregate:
    def __init__(self, id: str, user_id: str):
        self.id = id
        self.user_id = user_id
        self._items: list[OrderItem] = []
        self.status = "pending"
    
    def add_item(self, product_id: str, quantity: int):
        # Бизнес-логика валидации
        if self.status != "pending":
            raise ValueError("Cannot modify completed order")
        self._items.append(OrderItem(product_id, quantity))
    
    def complete(self):
        self.status = "completed"

# Query Model (Read) - оптимизирован для чтения
class OrderReadModel:
    def __init__(self, db):
        self.db = db
    
    def get_user_orders(self, user_id: str) -> list[dict]:
        # Денормализованная таблица, быстрый запрос
        return self.db.query("""
            SELECT id, total, status, created_at, 
                   items::json as items
            FROM order_read_view
            WHERE user_id = %s
        """, [user_id])
```

**Когда использовать CQRS**:
- ✅ Высокая нагрузка на чтение (социальные сети, аналитика)
- ✅ Разные требования к чтению и записи
- ✅ Нужна независимая масштабируемость read/write
- ❌ Простые CRUD приложения (overhead не оправдан)
- ❌ Низкая нагрузка (усложнение не нужно)

### Level 2: Как синхронизировать Read и Write модели в CQRS?
Объясни паттерны синхронизации: синхронная, асинхронная через события, eventual consistency.

**Answer**:
После записи в Command модель нужно обновить Read модель. Есть несколько подходов:

**1. Синхронная синхронизация (простой случай)**:
```python
class CreateOrderHandler:
    def __init__(self, order_repo: OrderRepository, read_model: OrderReadModel):
        self.order_repo = order_repo
        self.read_model = read_model
    
    def handle(self, command: CreateOrderCommand):
        # 1. Запись в Command модель
        order = Order(command.user_id)
        for item in command.items:
            order.add_item(item.product_id, item.quantity)
        self.order_repo.save(order)
        
        # 2. Синхронное обновление Read модели
        self.read_model.update_from_order(order)
        
        return order.id

class OrderReadModel:
    def update_from_order(self, order: Order):
        # Денормализация данных для чтения
        self.db.execute("""
            INSERT INTO order_read_view (id, user_id, total, status, items)
            VALUES (%s, %s, %s, %s, %s)
        """, [
            order.id,
            order.user_id,
            order.calculate_total(),
            order.status,
            json.dumps([item.to_dict() for item in order.items])
        ])
```

**Проблема**: Медленно, блокирует запись.

**2. Асинхронная синхронизация через события (рекомендуется)**:
```python
# Domain Event
class OrderCreatedEvent:
    def __init__(self, order_id: str, user_id: str, items: list, total: Decimal):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total = total
        self.timestamp = datetime.now()

# Command Handler публикует событие
class CreateOrderHandler:
    def __init__(self, order_repo: OrderRepository, event_bus: EventBus):
        self.order_repo = order_repo
        self.event_bus = event_bus
    
    def handle(self, command: CreateOrderCommand):
        order = Order(command.user_id)
        # ... создание заказа ...
        self.order_repo.save(order)
        
        # Публикуем событие (не блокирует)
        event = OrderCreatedEvent(
            order.id, order.user_id, 
            order.items, order.calculate_total()
        )
        self.event_bus.publish(event)
        
        return order.id

# Event Handler обновляет Read модель
class OrderReadModelUpdater:
    def __init__(self, read_model_db):
        self.db = read_model_db
    
    def handle(self, event: OrderCreatedEvent):
        # Асинхронное обновление Read модели
        self.db.execute("""
            INSERT INTO order_read_view (id, user_id, total, status, items, created_at)
            VALUES (%s, %s, %s, 'pending', %s, %s)
        """, [
            event.order_id,
            event.user_id,
            event.total,
            json.dumps(event.items),
            event.timestamp
        ])

# Event Bus подписывает handlers
event_bus.subscribe(OrderCreatedEvent, OrderReadModelUpdater().handle)
```

**Преимущества**:
- Запись не блокируется обновлением Read модели
- Можно масштабировать обработчики событий отдельно
- Eventual consistency - Read модель обновится "в итоге"

**3. Eventual Consistency - обработка задержек**:
```python
class OrderQueryService:
    def __init__(self, read_model: OrderReadModel, command_repo: OrderRepository):
        self.read_model = read_model
        self.command_repo = command_repo
    
    def get_order(self, order_id: str) -> dict:
        # Пробуем прочитать из Read модели
        order = self.read_model.find_by_id(order_id)
        
        if order:
            return order
        
        # Если нет в Read модели (еще не синхронизировалось),
        # читаем из Command модели (fallback)
        order_aggregate = self.command_repo.find_by_id(order_id)
        if order_aggregate:
            # Конвертируем в формат для чтения
            return {
                'id': order_aggregate.id,
                'user_id': order_aggregate.user_id,
                'status': order_aggregate.status,
                # ...
            }
        
        raise NotFoundError(f"Order {order_id} not found")
```

### Level 3: Что такое Event Sourcing и как его комбинировать с CQRS?
Объясни Event Sourcing: хранение событий вместо состояния, восстановление состояния, snapshots.

**Answer**:
Event Sourcing - вместо хранения текущего состояния, храним последовательность событий. Состояние восстанавливается replay'ем событий.

**Традиционный подход (State-based)**:
```python
# Храним текущее состояние
class Order:
    id: str
    user_id: str
    items: list
    status: str
    total: Decimal

# В БД:
# orders: id | user_id | status | total
# order_items: order_id | product_id | quantity
```

**Event Sourcing подход**:
```python
# Храним события
class OrderCreatedEvent:
    order_id: str
    user_id: str
    timestamp: datetime

class ItemAddedEvent:
    order_id: str
    product_id: str
    quantity: int
    timestamp: datetime

class OrderCompletedEvent:
    order_id: str
    timestamp: datetime

# В БД храним события:
# events: id | aggregate_id | event_type | event_data | version | timestamp
```

**Восстановление состояния из событий**:
```python
class OrderAggregate:
    def __init__(self, order_id: str):
        self.id = order_id
        self.user_id = None
        self._items: list[OrderItem] = []
        self.status = "pending"
        self._version = 0
    
    def apply_event(self, event):
        """Применяем событие к состоянию"""
        if isinstance(event, OrderCreatedEvent):
            self.user_id = event.user_id
        elif isinstance(event, ItemAddedEvent):
            self._items.append(OrderItem(event.product_id, event.quantity))
        elif isinstance(event, OrderCompletedEvent):
            self.status = "completed"
        
        self._version += 1
    
    @classmethod
    def from_events(cls, order_id: str, events: list) -> 'OrderAggregate':
        """Восстанавливаем состояние из событий"""
        aggregate = cls(order_id)
        for event in events:
            aggregate.apply_event(event)
        return aggregate

class OrderRepository:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    def save(self, aggregate: OrderAggregate):
        # Сохраняем новые события (не состояние!)
        new_events = aggregate.get_uncommitted_events()
        self.event_store.append_events(
            aggregate.id, 
            new_events, 
            expected_version=aggregate._version
        )
        aggregate.mark_events_as_committed()
    
    def find_by_id(self, order_id: str) -> OrderAggregate:
        # Загружаем события и восстанавливаем состояние
        events = self.event_store.get_events(order_id)
        return OrderAggregate.from_events(order_id, events)
```

**Проблема**: При большом количестве событий восстановление медленное.

**Решение: Snapshots**:
```python
class OrderSnapshot:
    def __init__(self, order_id: str, version: int, state: dict):
        self.order_id = order_id
        self.version = version  # Версия на момент snapshot
        self.state = state  # Сериализованное состояние

class OrderRepository:
    def find_by_id(self, order_id: str) -> OrderAggregate:
        # 1. Загружаем последний snapshot
        snapshot = self.event_store.get_latest_snapshot(order_id)
        
        # 2. Загружаем события после snapshot
        events = self.event_store.get_events_after(
            order_id, 
            snapshot.version if snapshot else 0
        )
        
        # 3. Восстанавливаем из snapshot + новые события
        if snapshot:
            aggregate = OrderAggregate.from_state(snapshot.state)
            aggregate._version = snapshot.version
        else:
            aggregate = OrderAggregate(order_id)
        
        for event in events:
            aggregate.apply_event(event)
        
        return aggregate
    
    def save(self, aggregate: OrderAggregate):
        # Сохраняем события
        self.event_store.append_events(...)
        
        # Периодически создаем snapshot (каждые N событий)
        if aggregate._version % 100 == 0:
            snapshot = OrderSnapshot(
                aggregate.id,
                aggregate._version,
                aggregate.to_dict()
            )
            self.event_store.save_snapshot(snapshot)
```

**Комбинация CQRS + Event Sourcing**:
```python
# Command Side: Event Sourcing
class CreateOrderHandler:
    def handle(self, command):
        order = Order(command.user_id)
        order.add_item(...)
        self.order_repo.save(order)  # Сохраняет события
        
        # Публикуем событие для Read модели
        self.event_bus.publish(OrderCreatedEvent(...))

# Read Side: Денормализованные таблицы
class OrderReadModel:
    def handle(self, event: OrderCreatedEvent):
        # Обновляем Read модель из события
        self.db.execute("INSERT INTO order_read_view...")
```

**Преимущества Event Sourcing**:
- Полная история изменений
- Audit log "из коробки"
- Можно "перемотать" время и посмотреть состояние на любую дату
- Легко добавить новые Read модели - просто подписаться на события

**Недостатки**:
- Сложность восстановления состояния
- Нужны snapshots для производительности
- Сложнее отлаживать

**Resources**:
- [Article] https://martinfowler.com/eaaDev/EventSourcing.html - Event Sourcing by Martin Fowler
- [Article] https://martinfowler.com/bliki/CQRS.html - CQRS by Martin Fowler
- [Video] https://www.youtube.com/watch?v=JHGkaShoyNs - Event Sourcing в Python
- [Code] https://github.com/eventstore/eventstore - EventStore database
- [Article] https://www.eventstore.com/blog/what-is-event-sourcing - Event Sourcing объяснение

**Related Concepts**: Domain Events, Event-Driven Architecture, Aggregate Pattern, Snapshot Pattern

---

## Concept: Microservices vs Monolith
**Tags**: microservices, monolith, distributed-systems, architecture-decision
**Estimated Time**: 40 minutes

### Level 1: Когда выбирать Monolith, а когда Microservices?
Объясни критерии выбора архитектуры и основные trade-offs.

**Answer**:
Выбор архитектуры зависит от контекста проекта, команды и требований.

**Monolith (монолит)** - одно приложение со всеми компонентами:

**Преимущества**:
- ✅ Простота разработки - один репозиторий, одна БД
- ✅ Простые транзакции - ACID гарантии в одной БД
- ✅ Легкое тестирование - запускаем все локально
- ✅ Простой деплой - один артефакт
- ✅ Нет проблем с распределенными транзакциями

**Недостатки**:
- ❌ Сложно масштабировать отдельные части
- ❌ Один баг может уронить все приложение
- ❌ Технологический стек фиксирован для всего
- ❌ Большая кодовая база усложняет разработку

**Microservices (микросервисы)** - множество независимых сервисов:

**Преимущества**:
- ✅ Независимое масштабирование каждого сервиса
- ✅ Независимый деплой - можно обновлять части системы отдельно
- ✅ Технологическое разнообразие - каждый сервис на своем стеке
- ✅ Изоляция ошибок - падение одного сервиса не ломает другие
- ✅ Команды работают независимо

**Недостатки**:
- ❌ Сложность - распределенная система сложнее монолита
- ❌ Сетевые задержки между сервисами
- ❌ Distributed transactions сложны (нужен Saga pattern)
- ❌ Операционная сложность - нужен orchestration (Kubernetes)
- ❌ Debugging сложнее - логи разбросаны

**Когда выбирать Monolith**:
- Стартап, MVP - нужна скорость разработки
- Маленькая команда (< 10 человек)
- Простое приложение без сложной бизнес-логики
- Нет требований к независимому масштабированию

**Когда выбирать Microservices**:
- Большая команда (> 50 человек) - нужна независимость
- Разные части системы имеют разные требования к масштабированию
- Нужна технологическая гибкость (разные языки/фреймворки)
- Разные команды владеют разными доменами

**Правило**: Начинай с Monolith, рефактори в Microservices когда появится реальная необходимость.

### Level 2: Как организовать коммуникацию между микросервисами?
Объясни синхронную (REST, gRPC) и асинхронную (Message Queue, Event Bus) коммуникацию.

**Answer**:
Коммуникация между микросервисами - критическая часть архитектуры.

**1. Синхронная коммуникация (REST/gRPC)**:

```python
# REST API клиент
import requests

class OrderService:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def create_order(self, user_id: str, items: list) -> dict:
        response = requests.post(
            f"{self.base_url}/orders",
            json={"user_id": user_id, "items": items},
            timeout=5  # Важно: таймаут!
        )
        response.raise_for_status()
        return response.json()

# Использование
class PaymentService:
    def __init__(self, order_service: OrderService):
        self.order_service = order_service
    
    def process_payment(self, order_id: str, card_token: str):
        # Синхронный вызов Order Service
        order = self.order_service.get_order(order_id)
        
        if order['total'] > 1000:
            # Дополнительная проверка
            pass
        
        # Обработка платежа
        return self.charge(order['total'], card_token)
```

**Проблемы синхронной коммуникации**:
- Каскадные падения - если Order Service упал, Payment Service тоже не работает
- Задержки накапливаются (latency)
- Таймауты и retry логика усложняют код

**Решение: Circuit Breaker**:
```python
from circuitbreaker import circuit

class OrderService:
    @circuit(failure_threshold=5, recovery_timeout=60)
    def get_order(self, order_id: str) -> dict:
        # Если 5 запросов подряд упали, circuit открывается
        # На 60 секунд все запросы сразу возвращают ошибку
        # без реального вызова сервиса
        response = requests.get(f"{self.base_url}/orders/{order_id}")
        return response.json()
```

**2. Асинхронная коммуникация (Message Queue)**:

```python
# Publisher (Order Service)
import pika

class OrderCreatedPublisher:
    def __init__(self, rabbitmq_connection):
        self.connection = rabbitmq_connection
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='orders',
            exchange_type='topic'
        )
    
    def publish_order_created(self, order_id: str, user_id: str, total: Decimal):
        message = {
            'order_id': order_id,
            'user_id': user_id,
            'total': float(total),
            'timestamp': datetime.now().isoformat()
        }
        self.channel.basic_publish(
            exchange='orders',
            routing_key='order.created',
            body=json.dumps(message)
        )

# Consumer (Payment Service)
class PaymentServiceConsumer:
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service
    
    def handle_order_created(self, ch, method, properties, body):
        message = json.loads(body)
        order_id = message['order_id']
        
        try:
            # Асинхронная обработка
            self.payment_service.process_pending_order(order_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            # В случае ошибки - negative ack, сообщение вернется в очередь
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

**Преимущества асинхронной коммуникации**:
- Decoupling - сервисы не знают друг о друге напрямую
- Resilience - если Payment Service упал, сообщения накапливаются в очереди
- Масштабируемость - можно добавить больше consumers

**3. Event-Driven Architecture (более продвинутый вариант)**:

```python
# Event Bus (централизованный)
class EventBus:
    def __init__(self):
        self._handlers: dict[str, list] = {}
    
    def subscribe(self, event_type: type, handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event):
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)

# Domain Event
class OrderCreatedEvent:
    def __init__(self, order_id: str, user_id: str, total: Decimal):
        self.order_id = order_id
        self.user_id = user_id
        self.total = total

# Handlers в разных сервисах
class PaymentServiceHandler:
    def handle(self, event: OrderCreatedEvent):
        # Обработка платежа
        pass

class NotificationServiceHandler:
    def handle(self, event: OrderCreatedEvent):
        # Отправка уведомления
        pass

# Подписка
event_bus.subscribe(OrderCreatedEvent, PaymentServiceHandler().handle)
event_bus.subscribe(OrderCreatedEvent, NotificationServiceHandler().handle)
```

### Level 3: Как обрабатывать распределенные транзакции в микросервисах?
Объясни Saga pattern, Two-Phase Commit, и компенсирующие транзакции.

**Answer**:
В микросервисах нет единой БД, поэтому классические ACID транзакции невозможны. Нужны паттерны для распределенных транзакций.

**Проблема**: Создание заказа требует:
1. Создать заказ (Order Service)
2. Заблокировать средства (Payment Service)
3. Резервировать товары (Inventory Service)
4. Отправить уведомление (Notification Service)

Если шаг 3 упадет, нужно откатить шаги 1 и 2.

**Решение 1: Saga Pattern (Choreography)**:

Каждый сервис знает что делать дальше и публикует события:

```python
# Order Service
class CreateOrderSaga:
    def execute(self, order_data: dict):
        order = self.create_order(order_data)
        self.event_bus.publish(OrderCreatedEvent(order.id, order.total))

# Payment Service подписан на OrderCreatedEvent
class PaymentService:
    def handle_order_created(self, event: OrderCreatedEvent):
        try:
            payment = self.reserve_payment(event.order_id, event.total)
            self.event_bus.publish(PaymentReservedEvent(event.order_id, payment.id))
        except InsufficientFundsError:
            self.event_bus.publish(OrderCancelledEvent(event.order_id, "Insufficient funds"))

# Inventory Service подписан на PaymentReservedEvent
class InventoryService:
    def handle_payment_reserved(self, event: PaymentReservedEvent):
        try:
            self.reserve_items(event.order_id)
            self.event_bus.publish(ItemsReservedEvent(event.order_id))
        except OutOfStockError:
            # Компенсирующая транзакция
            self.event_bus.publish(OrderCancelledEvent(event.order_id, "Out of stock"))
            self.event_bus.publish(ReleasePaymentEvent(event.order_id))

# Order Service подписан на OrderCancelledEvent
class OrderService:
    def handle_order_cancelled(self, event: OrderCancelledEvent):
        self.cancel_order(event.order_id)
```

**Проблема**: Сложно отследить весь flow, нет централизованного контроля.

**Решение 2: Saga Pattern (Orchestration)**:

Центральный оркестратор управляет всем процессом:

```python
class OrderOrchestrator:
    def __init__(self, order_service, payment_service, inventory_service):
        self.order_service = order_service
        self.payment_service = payment_service
        self.inventory_service = inventory_service
    
    def create_order(self, order_data: dict):
        saga_id = str(uuid.uuid4())
        steps = [
            Step('create_order', self.order_service.create, self.order_service.cancel),
            Step('reserve_payment', self.payment_service.reserve, self.payment_service.release),
            Step('reserve_items', self.inventory_service.reserve, self.inventory_service.release),
        ]
        
        executed_steps = []
        try:
            for step in steps:
                result = step.execute(order_data)
                executed_steps.append(step)
        except Exception as e:
            # Компенсируем выполненные шаги в обратном порядке
            for step in reversed(executed_steps):
                step.compensate(order_data)
            raise
        
        return saga_id

class Step:
    def __init__(self, name: str, execute_fn, compensate_fn):
        self.name = name
        self.execute_fn = execute_fn
        self.compensate_fn = compensate_fn
    
    def execute(self, data):
        return self.execute_fn(data)
    
    def compensate(self, data):
        return self.compensate_fn(data)
```

**Решение 3: Two-Phase Commit (2PC) - не рекомендуется**:

Координатор управляет двухфазным коммитом:

```python
class TwoPhaseCommitCoordinator:
    def execute_transaction(self, participants: list[Service]):
        transaction_id = str(uuid.uuid4())
        
        # Phase 1: Prepare
        prepared = []
        for participant in participants:
            try:
                if participant.prepare(transaction_id):
                    prepared.append(participant)
                else:
                    # Abort всех
                    for p in prepared:
                        p.abort(transaction_id)
                    return False
            except Exception:
                # Abort всех
                for p in prepared:
                    p.abort(transaction_id)
                return False
        
        # Phase 2: Commit (если все подготовились)
        for participant in prepared:
            participant.commit(transaction_id)
        
        return True
```

**Проблемы 2PC**:
- Блокирующий протокол - все ждут самого медленного
- Single point of failure - координатор
- Не подходит для высоконагруженных систем

**Рекомендация**: Используй Saga pattern для микросервисов. 2PC только для критичных финансовых операций.

### Level 4: Как проектировать границы микросервисов (Bounded Contexts)?
Объясни Domain-Driven Design подход к разбиению на сервисы, Shared Kernel, и Anti-Corruption Layer.

**Answer**:
Правильное разбиение на микросервисы критично. Неправильные границы приводят к тесной связанности.

**1. Разбиение по Domain (DDD подход)**:

```python
# ❌ Плохо: Разбиение по техническим слоям
# services/
#   user-db-service/
#   user-api-service/
#   user-cache-service/

# ✅ Хорошо: Разбиение по бизнес-доменам
# services/
#   user-service/        # Весь контекст пользователей
#   order-service/       # Весь контекст заказов
#   payment-service/     # Весь контекст платежей
```

**2. Bounded Context - четкие границы доменов**:

```python
# User Service (Bounded Context: User Management)
class User:
    """User в контексте управления пользователями"""
    def __init__(self, id: str, email: str, profile: UserProfile):
        self.id = id
        self.email = email
        self.profile = profile  # Полный профиль
    
    def update_profile(self, new_profile: UserProfile):
        # Бизнес-правила пользователя
        pass

# Order Service (Bounded Context: Order Management)
class Order:
    """Order знает только минимум о User"""
    def __init__(self, id: str, user_id: str, items: list):
        self.id = id
        self.user_id = user_id  # Только ID, не весь объект User
        self.items = items
    
    def get_user_info(self) -> dict:
        # Запрашиваем у User Service только нужные данные
        user_service_client.get_user_summary(self.user_id)
```

**3. Shared Kernel - общие модели (осторожно!)**:

```python
# shared/
#   models/
#     money.py          # Value Object - можно шарить
#     address.py        # Value Object - можно шарить

# ❌ НЕ шарим Entities между контекстами
# shared/
#   models/
#     user.py          # Плохо! User должен быть в своем контексте
```

**4. Anti-Corruption Layer (ACL)**:

Когда нужно интегрироваться с legacy системой или внешним API:

```python
# External Service (legacy система)
class LegacyUserAPI:
    def get_user(self, user_id: str) -> dict:
        # Возвращает данные в старом формате
        return {
            'usr_id': user_id,  # Старое поле
            'usr_email': '...',  # Старое поле
            'usr_data': {...}    # Сложная структура
        }

# Anti-Corruption Layer - адаптер
class UserServiceAdapter:
    def __init__(self, legacy_api: LegacyUserAPI):
        self.legacy_api = legacy_api
    
    def get_user(self, user_id: str) -> User:
        # Преобразуем старый формат в наш доменный объект
        legacy_data = self.legacy_api.get_user(user_id)
        
        return User(
            id=legacy_data['usr_id'],
            email=legacy_data['usr_email'],
            profile=self._map_profile(legacy_data['usr_data'])
        )
    
    def _map_profile(self, legacy_data: dict) -> UserProfile:
        # Сложная логика маппинга
        # Изолирует наш код от legacy формата
        pass

# Наш сервис использует только наш доменный объект
class UserService:
    def __init__(self, adapter: UserServiceAdapter):
        self.adapter = adapter
    
    def get_user(self, user_id: str) -> User:
        # Работаем только с нашими моделями
        return self.adapter.get_user(user_id)
```

**5. Context Mapping - визуализация связей**:

```
[User Context] ----U/D----> [Order Context]
     |                           |
     | (User ID only)            |
     |                           |
     v                           v
[Payment Context] <--U/D--> [Shipping Context]

U/D = Upstream/Downstream
```

**Upstream** (поставщик данных) - Order Context зависит от User Context.
**Downstream** (потребитель) - Order Context потребляет данные из User Context.

**Правила**:
- Downstream НЕ должен изменять Upstream модель
- Используй события для синхронизации вместо прямых вызовов
- Минимизируй количество Upstream зависимостей

**6. Практический пример правильного разбиения**:

```python
# E-commerce система

# User Service (Core Domain)
class UserService:
    """Управление пользователями, аутентификация"""
    def register_user(self, email: str, password: str) -> User
    def authenticate(self, email: str, password: str) -> Token
    def get_user_profile(self, user_id: str) -> UserProfile

# Catalog Service (Supporting Domain)
class CatalogService:
    """Каталог товаров"""
    def get_product(self, product_id: str) -> Product
    def search_products(self, query: str) -> list[Product]

# Order Service (Core Domain)
class OrderService:
    """Обработка заказов"""
    def create_order(self, user_id: str, items: list) -> Order
    def get_order(self, order_id: str) -> Order
    # Зависит от User Service (user_id) и Catalog Service (product_id)

# Payment Service (Supporting Domain)
class PaymentService:
    """Обработка платежей"""
    def process_payment(self, order_id: str, card_token: str) -> Payment
    # Зависит от Order Service

# Notification Service (Generic Subdomain)
class NotificationService:
    """Отправка уведомлений"""
    def send_email(self, to: str, subject: str, body: str)
    # Независимый сервис, подписан на события
```

**Критерии правильного разбиения**:
- ✅ Каждый сервис имеет четкую бизнес-ответственность
- ✅ Минимум связей между сервисами
- ✅ Можно разрабатывать и деплоить независимо
- ✅ Разные команды могут владеть разными сервисами

**Resources**:
- [Book] Building Microservices by Sam Newman - Классика по микросервисам
- [Article] https://martinfowler.com/articles/microservices.html - Microservices by Martin Fowler
- [Article] https://microservices.io/patterns/data/saga.html - Saga Pattern
- [Video] https://www.youtube.com/watch?v=yPvef9R3k-M - Distributed Systems в Python
- [Article] https://www.nginx.com/blog/building-microservices-inter-communication/ - Service Communication Patterns

**Related Concepts**: Domain-Driven Design, Event-Driven Architecture, API Gateway, Service Mesh, Distributed Tracing

---

## Concept: SOLID Principles в контексте архитектуры
**Tags**: solid, design-principles, clean-code, maintainability
**Estimated Time**: 45 minutes

### Level 1: Что такое SOLID принципы и зачем они нужны?
Объясни все пять принципов SOLID с простыми примерами.

**Answer**:
SOLID - пять принципов объектно-ориентированного дизайна для создания поддерживаемого кода.

**S - Single Responsibility Principle (Принцип единственной ответственности)**:
Класс должен иметь только одну причину для изменения.

```python
# ❌ Плохо: Класс делает слишком много
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
    def save_to_database(self):
        # Работа с БД
        pass
    
    def send_email(self, message: str):
        # Отправка email
        pass
    
    def validate(self):
        # Валидация
        pass

# ✅ Хорошо: Разделение ответственностей
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user: User):
        # Только работа с БД
        pass

class EmailService:
    def send(self, to: str, message: str):
        # Только отправка email
        pass

class UserValidator:
    def validate(self, user: User) -> bool:
        # Только валидация
        pass
```

**O - Open/Closed Principle (Принцип открытости/закрытости)**:
Классы должны быть открыты для расширения, но закрыты для модификации.

```python
# ❌ Плохо: Нужно менять код при добавлении нового типа
class AreaCalculator:
    def calculate(self, shape):
        if isinstance(shape, Rectangle):
            return shape.width * shape.height
        elif isinstance(shape, Circle):
            return 3.14 * shape.radius ** 2
        # Придется добавлять новый elif для каждого типа

# ✅ Хорошо: Расширяемость через полиморфизм
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Rectangle(Shape):
    def area(self) -> float:
        return self.width * self.height

class Circle(Shape):
    def area(self) -> float:
        return 3.14 * self.radius ** 2

class AreaCalculator:
    def calculate(self, shape: Shape) -> float:
        # Не нужно менять этот код при добавлении новых типов
        return shape.area()
```

**L - Liskov Substitution Principle (Принцип подстановки Лисков)**:
Объекты подклассов должны заменять объекты базового класса без нарушения функциональности.

```python
# ❌ Плохо: Нарушение LSP
class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def set_width(self, width: float):
        self.width = width
    
    def set_height(self, height: float):
        self.height = height

class Square(Rectangle):
    def set_width(self, width: float):
        self.width = width
        self.height = width  # Нарушение! Меняет и height
    
    def set_height(self, height: float):
        self.height = height
        self.width = height  # Нарушение! Меняет и width

# Код ожидает Rectangle, но Square ведет себя по-другому
def test_rectangle(rect: Rectangle):
    rect.set_width(5)
    rect.set_height(4)
    assert rect.width == 5  # Упадет для Square!

# ✅ Хорошо: Правильная иерархия
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Rectangle(Shape):
    def area(self) -> float:
        return self.width * self.height

class Square(Shape):
    def area(self) -> float:
        return self.side ** 2
```

**I - Interface Segregation Principle (Принцип разделения интерфейса)**:
Клиенты не должны зависеть от интерфейсов, которые они не используют.

```python
# ❌ Плохо: Толстый интерфейс
class Worker(ABC):
    @abstractmethod
    def work(self):
        pass
    
    @abstractmethod
    def eat(self):
        pass

class Human(Worker):
    def work(self):
        print("Working...")
    
    def eat(self):
        print("Eating...")

class Robot(Worker):
    def work(self):
        print("Working...")
    
    def eat(self):
        raise NotImplementedError("Robots don't eat!")  # Проблема!

# ✅ Хорошо: Разделенные интерфейсы
class Workable(ABC):
    @abstractmethod
    def work(self):
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self):
        pass

class Human(Workable, Eatable):
    def work(self):
        print("Working...")
    
    def eat(self):
        print("Eating...")

class Robot(Workable):
    def work(self):
        print("Working...")
    # Не нужно реализовывать eat()
```

**D - Dependency Inversion Principle (Принцип инверсии зависимостей)**:
Зависимости должны быть направлены на абстракции, а не на конкретные реализации.

```python
# ❌ Плохо: Зависимость от конкретной реализации
class MySQLDatabase:
    def save(self, data):
        print("Saving to MySQL...")

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Жесткая зависимость
    
    def create_user(self, user_data):
        self.db.save(user_data)

# ✅ Хорошо: Зависимость от абстракции
class Database(ABC):
    @abstractmethod
    def save(self, data):
        pass

class MySQLDatabase(Database):
    def save(self, data):
        print("Saving to MySQL...")

class PostgreSQLDatabase(Database):
    def save(self, data):
        print("Saving to PostgreSQL...")

class UserService:
    def __init__(self, db: Database):  # Зависимость от абстракции
        self.db = db
    
    def create_user(self, user_data):
        self.db.save(user_data)

# Можно легко заменить реализацию
service = UserService(PostgreSQLDatabase())
```

### Level 2: Как применять SOLID в реальных проектах?
Покажи практические примеры применения SOLID в веб-приложениях и API.

**Answer**:
Рассмотрим реальный пример: система обработки заказов.

**Пример: Order Processing System**:

```python
# 1. Single Responsibility - разделяем ответственности
class Order:
    """Только бизнес-логика заказа"""
    def __init__(self, order_id: str, items: list[OrderItem]):
        self.id = order_id
        self.items = items
        self.status = "pending"
    
    def calculate_total(self) -> Decimal:
        return sum(item.subtotal() for item in self.items)
    
    def mark_as_paid(self):
        if self.status != "pending":
            raise ValueError("Only pending orders can be marked as paid")
        self.status = "paid"

class OrderRepository:
    """Только работа с БД"""
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, order: Order):
        self.db.execute("INSERT INTO orders...")
    
    def find_by_id(self, order_id: str) -> Order:
        # Загрузка из БД
        pass

class OrderValidator:
    """Только валидация"""
    def validate(self, order: Order) -> tuple[bool, list[str]]:
        errors = []
        if not order.items:
            errors.append("Order must have at least one item")
        if order.calculate_total() <= 0:
            errors.append("Order total must be positive")
        return len(errors) == 0, errors

# 2. Open/Closed - расширяемость через стратегии
class PaymentMethod(ABC):
    @abstractmethod
    def process(self, amount: Decimal) -> PaymentResult:
        pass

class CreditCardPayment(PaymentMethod):
    def process(self, amount: Decimal) -> PaymentResult:
        # Логика обработки карты
        pass

class PayPalPayment(PaymentMethod):
    def process(self, amount: Decimal) -> PaymentResult:
        # Логика PayPal
        pass

class PaymentProcessor:
    """Не нужно менять при добавлении новых методов оплаты"""
    def __init__(self, payment_method: PaymentMethod):
        self.payment_method = payment_method
    
    def process_order_payment(self, order: Order) -> PaymentResult:
        return self.payment_method.process(order.calculate_total())

# 3. Liskov Substitution - правильная иерархия
class NotificationService(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        """Отправляет уведомление, возвращает успех"""
        pass

class EmailNotificationService(NotificationService):
    def send(self, recipient: str, message: str) -> bool:
        # Отправка email
        return True

class SMSNotificationService(NotificationService):
    def send(self, recipient: str, message: str) -> bool:
        # Отправка SMS
        return True

# Можно заменить любую реализацию без изменения кода
class OrderService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    def notify_order_created(self, order: Order):
        # Работает с любой реализацией NotificationService
        self.notification_service.send(
            order.customer_email,
            f"Order {order.id} created"
        )

# 4. Interface Segregation - тонкие интерфейсы
class ReadableRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: str):
        pass

class WritableRepository(ABC):
    @abstractmethod
    def save(self, entity):
        pass

class DeletableRepository(ABC):
    @abstractmethod
    def delete(self, id: str):
        pass

# Класс использует только нужные интерфейсы
class OrderRepository(ReadableRepository, WritableRepository):
    def find_by_id(self, id: str) -> Order:
        pass
    
    def save(self, order: Order):
        pass
    # Не нужно реализовывать delete()

class LogRepository(ReadableRepository):
    """Только чтение логов"""
    def find_by_id(self, id: str):
        pass
    # Не нужно save() или delete()

# 5. Dependency Inversion - зависимости от абстракций
class OrderService:
    """Высокоуровневый модуль"""
    def __init__(
        self,
        order_repo: OrderRepository,  # Абстракция
        payment_processor: PaymentProcessor,  # Абстракция
        notification_service: NotificationService  # Абстракция
    ):
        self.order_repo = order_repo
        self.payment_processor = payment_processor
        self.notification_service = notification_service
    
    def create_and_process_order(self, order_data: dict) -> Order:
        # Бизнес-логика не зависит от деталей реализации
        order = Order(order_data['id'], order_data['items'])
        
        # Валидация
        validator = OrderValidator()
        is_valid, errors = validator.validate(order)
        if not is_valid:
            raise ValueError(f"Invalid order: {errors}")
        
        # Сохранение
        self.order_repo.save(order)
        
        # Обработка платежа
        result = self.payment_processor.process_order_payment(order)
        if result.success:
            order.mark_as_paid()
            self.order_repo.save(order)
            
            # Уведомление
            self.notification_service.send(
                order.customer_email,
                f"Order {order.id} processed successfully"
            )
        
        return order
```

**Практические советы**:
- Начинай с Single Responsibility - это основа остальных принципов
- Используй абстракции (ABC, Protocol) для Dependency Inversion
- Разбивай большие интерфейсы на маленькие (Interface Segregation)
- Тестируй заменяемость подклассов (Liskov Substitution)

### Level 3: Как SOLID принципы связаны с архитектурными паттернами?
Объясни связь SOLID с Repository, Factory, Strategy, Observer паттернами.

**Answer**:
SOLID принципы лежат в основе многих паттернов проектирования.

**1. Repository Pattern и Dependency Inversion**:

```python
# Repository Pattern реализует DIP
class UserRepository(ABC):  # Абстракция
    @abstractmethod
    def find_by_id(self, user_id: str) -> User:
        pass

class PostgreSQLUserRepository(UserRepository):  # Конкретная реализация
    def find_by_id(self, user_id: str) -> User:
        # Детали работы с PostgreSQL
        pass

class UserService:
    def __init__(self, user_repo: UserRepository):  # Зависит от абстракции
        self.user_repo = user_repo  # DIP в действии
```

**2. Strategy Pattern и Open/Closed Principle**:

```python
# Strategy Pattern позволяет расширять без модификации (OCP)
class SortingStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list:
        pass

class QuickSortStrategy(SortingStrategy):
    def sort(self, data: list) -> list:
        # Quick sort реализация
        pass

class MergeSortStrategy(SortingStrategy):
    def sort(self, data: list) -> list:
        # Merge sort реализация
        pass

class DataProcessor:
    def __init__(self, sorting_strategy: SortingStrategy):
        self.sorting_strategy = sorting_strategy  # Можно заменить стратегию
    
    def process(self, data: list) -> list:
        # Не нужно менять этот код при добавлении новых стратегий
        sorted_data = self.sorting_strategy.sort(data)
        return sorted_data
```

**3. Factory Pattern и Dependency Inversion**:

```python
# Factory Pattern создает объекты через абстракции (DIP)
class DatabaseFactory(ABC):
    @abstractmethod
    def create_connection(self) -> Database:
        pass

class PostgreSQLFactory(DatabaseFactory):
    def create_connection(self) -> Database:
        return PostgreSQLConnection()

class MySQLFactory(DatabaseFactory):
    def create_connection(self) -> Database:
        return MySQLConnection()

class Application:
    def __init__(self, db_factory: DatabaseFactory):
        self.db = db_factory.create_connection()  # Зависит от абстракции
```

**4. Observer Pattern и Interface Segregation**:

```python
# Observer Pattern с разделенными интерфейсами (ISP)
class EventListener(ABC):
    @abstractmethod
    def on_event(self, event: Event):
        pass

class EmailListener(EventListener):
    def on_event(self, event: Event):
        # Отправка email
        pass

class LoggingListener(EventListener):
    def on_event(self, event: Event):
        # Логирование
        pass

class EventPublisher:
    def __init__(self):
        self._listeners: list[EventListener] = []
    
    def subscribe(self, listener: EventListener):
        self._listeners.append(listener)
    
    def publish(self, event: Event):
        for listener in self._listeners:
            listener.on_event(event)  # Каждый listener реализует только нужный интерфейс
```

**5. Command Pattern и Single Responsibility**:

```python
# Command Pattern разделяет ответственности (SRP)
class Command(ABC):
    """Только выполнение команды"""
    @abstractmethod
    def execute(self):
        pass

class CreateUserCommand(Command):
    def __init__(self, user_repo: UserRepository, user_data: dict):
        self.user_repo = user_repo
        self.user_data = user_data
    
    def execute(self):
        user = User(**self.user_data)
        self.user_repo.save(user)

class CommandInvoker:
    """Только вызов команд"""
    def __init__(self):
        self.history: list[Command] = []
    
    def execute(self, command: Command):
        command.execute()
        self.history.append(command)
```

**6. Комбинация паттернов с SOLID**:

```python
# Пример: Order Processing с несколькими паттернами

# 1. Repository (DIP)
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order):
        pass

# 2. Strategy для разных способов обработки (OCP)
class OrderProcessingStrategy(ABC):
    @abstractmethod
    def process(self, order: Order) -> ProcessingResult:
        pass

class StandardOrderProcessing(OrderProcessingStrategy):
    def process(self, order: Order) -> ProcessingResult:
        # Стандартная обработка
        pass

class ExpressOrderProcessing(OrderProcessingStrategy):
    def process(self, order: Order) -> ProcessingResult:
        # Экспресс обработка
        pass

# 3. Factory для создания стратегий (DIP)
class ProcessingStrategyFactory(ABC):
    @abstractmethod
    def create_strategy(self, order_type: str) -> OrderProcessingStrategy:
        pass

# 4. Observer для уведомлений (ISP)
class OrderEventListener(ABC):
    @abstractmethod
    def on_order_created(self, order: Order):
        pass

# 5. Service использует все через абстракции (DIP, SRP)
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,  # DIP
        strategy_factory: ProcessingStrategyFactory,  # DIP
        event_publisher: EventPublisher  # DIP
    ):
        self.order_repo = order_repo
        self.strategy_factory = strategy_factory
        self.event_publisher = event_publisher
    
    def create_order(self, order_data: dict) -> Order:
        order = Order(**order_data)
        
        # Сохранение (Repository)
        self.order_repo.save(order)
        
        # Обработка (Strategy)
        strategy = self.strategy_factory.create_strategy(order.type)
        result = strategy.process(order)
        
        # Уведомление (Observer)
        self.event_publisher.publish(OrderCreatedEvent(order))
        
        return order
```

**Вывод**: SOLID принципы не изолированы - они работают вместе и лежат в основе паттернов проектирования.

### Level 4: Как применять SOLID в распределенных системах и микросервисах?
Объясни применение SOLID на уровне архитектуры сервисов, API design, и межсервисной коммуникации.

**Answer**:
SOLID принципы применимы не только к классам, но и к архитектуре сервисов.

**1. Single Responsibility на уровне сервисов**:

```python
# ❌ Плохо: Один сервис делает все
class MegaService:
    def create_user(self, ...): pass
    def create_order(self, ...): pass
    def process_payment(self, ...): pass
    def send_notification(self, ...): pass

# ✅ Хорошо: Каждый сервис - одна ответственность
class UserService:
    """Только управление пользователями"""
    def create_user(self, ...): pass
    def update_user(self, ...): pass
    def delete_user(self, ...): pass

class OrderService:
    """Только управление заказами"""
    def create_order(self, ...): pass
    def update_order(self, ...): pass

class PaymentService:
    """Только обработка платежей"""
    def process_payment(self, ...): pass
```

**2. Open/Closed для API версионирования**:

```python
# API версионирование позволяет расширять без ломания существующих клиентов (OCP)
class OrderAPI:
    # v1 - базовая версия
    @app.route('/api/v1/orders', methods=['POST'])
    def create_order_v1(self, data: dict):
        # Старая логика
        pass
    
    # v2 - расширенная версия (не ломает v1)
    @app.route('/api/v2/orders', methods=['POST'])
    def create_order_v2(self, data: dict):
        # Новая логика с дополнительными полями
        # Старые клиенты продолжают работать с v1
        pass
```

**3. Liskov Substitution для API контрактов**:

```python
# Клиенты должны работать с любой реализацией API, соответствующей контракту
class PaymentGatewayAPI(ABC):
    """Контракт API платежного шлюза"""
    @abstractmethod
    def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        """Все реализации должны следовать этому контракту"""
        pass

class StripePaymentAPI(PaymentGatewayAPI):
    def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        # Реализация Stripe
        # Должна работать как замена любого PaymentGatewayAPI
        pass

class PayPalPaymentAPI(PaymentGatewayAPI):
    def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        # Реализация PayPal
        # Можно заменить Stripe без изменения клиентского кода
        pass

class PaymentService:
    def __init__(self, payment_api: PaymentGatewayAPI):
        self.payment_api = payment_api  # Работает с любой реализацией
    
    def process(self, order: Order, card_token: str):
        # Не знает о конкретной реализации
        return self.payment_api.charge(order.total, card_token)
```

**4. Interface Segregation для API endpoints**:

```python
# ❌ Плохо: Один большой API со всеми методами
class UserAPI:
    def get_user(self, ...): pass
    def create_user(self, ...): pass
    def update_user(self, ...): pass
    def delete_user(self, ...): pass
    def get_user_orders(self, ...): pass  # Не относится к User!
    def get_user_payments(self, ...): pass  # Не относится к User!

# ✅ Хорошо: Разделенные API по ответственности
class UserAPI:
    """Только операции с пользователями"""
    def get_user(self, ...): pass
    def create_user(self, ...): pass
    def update_user(self, ...): pass
    def delete_user(self, ...): pass

class OrderAPI:
    """Только операции с заказами"""
    def get_user_orders(self, user_id: str): pass  # Но через User ID

class PaymentAPI:
    """Только операции с платежами"""
    def get_user_payments(self, user_id: str): pass
```

**5. Dependency Inversion для межсервисной коммуникации**:

```python
# Сервисы зависят от абстракций (контрактов), а не от конкретных реализаций

# Контракт (интерфейс) - общий для всех сервисов
class UserServiceContract(ABC):
    """Контракт User Service API"""
    @abstractmethod
    def get_user(self, user_id: str) -> UserDTO:
        pass

# Реализация контракта (может быть REST, gRPC, GraphQL)
class UserServiceRESTClient(UserServiceContract):
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_user(self, user_id: str) -> UserDTO:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        return UserDTO(**response.json())

class UserServicegRPCClient(UserServiceContract):
    def __init__(self, stub):
        self.stub = stub
    
    def get_user(self, user_id: str) -> UserDTO:
        response = self.stub.GetUser(user_id_pb2.UserId(id=user_id))
        return UserDTO.from_proto(response)

# Order Service зависит от контракта, а не от реализации
class OrderService:
    def __init__(self, user_service: UserServiceContract):  # Зависит от абстракции
        self.user_service = user_service
    
    def create_order(self, user_id: str, items: list):
        # Использует контракт, не знает о REST/gRPC
        user = self.user_service.get_user(user_id)
        # Создание заказа...
```

**6. Практический пример: E-commerce система**:

```python
# Архитектура с SOLID принципами

# 1. Domain Layer (Entities) - SRP
class Order:
    """Только бизнес-логика заказа"""
    def calculate_total(self): pass
    def mark_as_paid(self): pass

# 2. Application Layer (Use Cases) - SRP, DIP
class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,  # DIP
        user_service: UserServiceContract,  # DIP
        inventory_service: InventoryServiceContract  # DIP
    ):
        self.order_repo = order_repo
        self.user_service = user_service
        self.inventory_service = inventory_service
    
    def execute(self, command: CreateOrderCommand):
        # Бизнес-логика не зависит от деталей реализации сервисов
        user = self.user_service.get_user(command.user_id)
        
        # Проверка наличия товаров
        for item in command.items:
            available = self.inventory_service.check_availability(
                item.product_id, item.quantity
            )
            if not available:
                raise ValueError(f"Product {item.product_id} not available")
        
        # Создание заказа
        order = Order(command.user_id, command.items)
        self.order_repo.save(order)
        return order

# 3. Infrastructure Layer (Adapters) - реализуют контракты
class RESTUserServiceClient(UserServiceContract):
    """Адаптер для REST API"""
    def get_user(self, user_id: str) -> UserDTO:
        # Детали HTTP запроса
        pass

class gRPCInventoryServiceClient(InventoryServiceContract):
    """Адаптер для gRPC API"""
    def check_availability(self, product_id: str, quantity: int) -> bool:
        # Детали gRPC вызова
        pass

# 4. Composition Root - собираем зависимости
def create_order_service():
    # Можно легко заменить реализации
    user_service = RESTUserServiceClient("http://user-service")
    inventory_service = gRPCInventoryServiceClient("inventory-service:50051")
    order_repo = PostgreSQLOrderRepository(db_connection)
    
    return CreateOrderUseCase(order_repo, user_service, inventory_service)
```

**Преимущества применения SOLID на уровне архитектуры**:
- Легко заменить один сервис на другой (DIP)
- Каждый сервис имеет четкую ответственность (SRP)
- Можно расширять функциональность без изменения существующих сервисов (OCP)
- API контракты четко определены (LSP, ISP)

**Resources**:
- [Book] Clean Architecture by Robert C. Martin - SOLID и архитектура
- [Article] https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html - Clean Architecture
- [Video] https://www.youtube.com/watch?v=TMuno5RZNeE - SOLID Principles
- [Article] https://martinfowler.com/articles/injection.html - Dependency Injection
- [Code] https://github.com/cosmic-python/code - Примеры применения SOLID

**Related Concepts**: Design Patterns, Dependency Injection, API Design, Service Contracts, Microservices Architecture

