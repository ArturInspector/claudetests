# Topic: RSA и Алгебра

## Concept: RSA Криптография
**Tags**: cryptography, rsa, number-theory, public-key, encryption
**Estimated Time**: 30 minutes

### Level 1: Что такое RSA и как он работает?
Объясни основные принципы RSA: генерация ключей, шифрование, расшифрование.

**Answer**:
RSA (Rivest-Shamir-Adleman) - алгоритм асимметричного шифрования с открытым ключом.

**Основные шаги**:

1. **Генерация ключей**:
   - Выбираем два больших простых числа `p` и `q`
   - Вычисляем `n = p * q` (модуль)
   - Вычисляем `φ(n) = (p-1)(q-1)` (функция Эйлера)
   - Выбираем `e` такое, что `1 < e < φ(n)` и `gcd(e, φ(n)) = 1` (открытая экспонента)
   - Вычисляем `d` такое, что `e * d ≡ 1 (mod φ(n))` (закрытая экспонента)

2. **Публичный ключ**: `(e, n)`
3. **Приватный ключ**: `(d, n)`

**Шифрование**: `c = m^e mod n` (где `m` - сообщение)
**Расшифрование**: `m = c^d mod n`

**Пример (упрощенный, маленькие числа)**:
```python
# Генерация ключей
p, q = 61, 53  # Простые числа
n = p * q  # 3233
φ = (p-1) * (q-1)  # 3120
e = 17  # Взаимно простое с φ
d = pow(e, -1, φ)  # Модульная инверсия: 2753

# Публичный ключ: (17, 3233)
# Приватный ключ: (2753, 3233)

# Шифрование
m = 65  # Сообщение
c = pow(m, e, n)  # 2790

# Расшифрование
m_decrypted = pow(c, d, n)  # 65
```

**Почему это работает**: Основано на сложности факторизации больших чисел и малой теореме Ферма.

### Level 2: Как работает модульная арифметика в RSA?
Объясни модульную инверсию, расширенный алгоритм Евклида, и китайскую теорему об остатках.

**Answer**:
Модульная арифметика - основа RSA. Работаем с остатками от деления.

**Модульная инверсия**:
Число `d` является обратным к `e` по модулю `n`, если `e * d ≡ 1 (mod n)`.

```python
def mod_inverse(a, m):
    """Находит x такой, что a*x ≡ 1 (mod m)"""
    # Используем расширенный алгоритм Евклида
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError("Inverse doesn't exist")
    return (x % m + m) % m

# Пример
e, φ = 17, 3120
d = mod_inverse(e, φ)  # 2753
assert (e * d) % φ == 1
```

**Расширенный алгоритм Евклида**:
Находит НОД и коэффициенты Безу: `gcd(a, b) = a*x + b*y`

```python
def extended_gcd(a, b):
    """Возвращает (gcd, x, y) такие что a*x + b*y = gcd(a, b)"""
    if a == 0:
        return b, 0, 1
    
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

# Пример: gcd(17, 3120) = 1 = 17*2753 + 3120*(-15)
gcd, x, y = extended_gcd(17, 3120)
# x = 2753 (это и есть модульная инверсия 17 по модулю 3120)
```

**Китайская теорема об остатках (CRT)**:
Ускоряет вычисления в RSA. Вместо `m^d mod n`, вычисляем:
- `m^d mod p`
- `m^d mod q`
- Объединяем результаты

```python
def rsa_decrypt_crt(c, d, p, q):
    """Расшифрование RSA с использованием CRT"""
    n = p * q
    dp = d % (p - 1)
    dq = d % (q - 1)
    
    # Вычисляем по модулям p и q
    mp = pow(c, dp, p)
    mq = pow(c, dq, q)
    
    # Объединяем через CRT
    # Находим x такой, что x ≡ mp (mod p) и x ≡ mq (mod q)
    _, inv_q, _ = extended_gcd(q, p)
    m = (mp + p * ((mq - mp) * inv_q % p)) % n
    return m

# Быстрее чем прямое вычисление m^d mod n для больших чисел
```

### Level 3: Почему RSA безопасен? Атаки и защита
Объясни почему факторизация сложна, атаки на малую экспоненту, timing attacks, и padding схемы.

**Answer**:
Безопасность RSA основана на сложности факторизации `n = p * q`. Если злоумышленник найдет `p` и `q`, он вычислит `d`.

**Почему факторизация сложна**:
- Для `n` из 2048 бит нужно проверить ~2^1024 возможных делителей
- Лучшие алгоритмы (General Number Field Sieve) имеют сложность `exp(O((log n)^(1/3)))`
- Квантовые компьютеры могут использовать алгоритм Шора (O((log n)^3)), но пока не практично

**Атака на малую экспоненту `e`**:
Если `e` маленькое (например, 3) и сообщение короткое:

```python
# ❌ Опасно: e=3, m маленькое
e, n = 3, 3233
m = 10
c = pow(m, e, n)  # 1000

# Если m^e < n, то c = m^e (без модуля)
# Можно просто извлечь корень: m = c^(1/e)
m_attacked = round(c ** (1/e))  # 10 - взломано!
```

**Защита**: Использовать `e = 65537` (стандарт) и padding (OAEP).

**Timing Attack**:
Измеряя время выполнения, можно узнать биты приватного ключа:

```python
# Уязвимая реализация
def mod_pow_vulnerable(base, exp, mod):
    result = 1
    for bit in bin(exp)[2:]:  # Перебираем биты экспоненты
        result = (result * result) % mod
        if bit == '1':
            result = (result * base) % mod
        # Время выполнения зависит от битов exp!
    return result
```

**Защита**: Constant-time операции, blinding:

```python
def mod_pow_safe(base, exp, mod):
    """Constant-time возведение в степень"""
    result = 1
    base = base % mod
    # Всегда выполняем одинаковое количество операций
    for _ in range(exp.bit_length()):
        if exp & 1:
            result = (result * base) % mod
        exp >>= 1
        base = (base * base) % mod
    return result
```

**OAEP Padding**:
Защищает от атак на малую экспоненту и делает сообщения случайными:

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Генерация ключей
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Шифрование с OAEP
message = b"Secret message"
ciphertext = public_key.encrypt(
    message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Расшифрование
plaintext = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

### Level 4: Реализация RSA с нуля и оптимизации
Покажи полную реализацию RSA, тест Миллера-Рабина для генерации простых чисел, и оптимизации.

**Answer**:
Полная реализация RSA с генерацией простых чисел и оптимизациями.

```python
import random
import math

def miller_rabin(n, k=40):
    """Тест Миллера-Рабина на простоту"""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Записываем n-1 = d * 2^r
    r = 0
    d = n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # k раундов теста
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True

def generate_prime(bits):
    """Генерирует простое число заданной длины"""
    while True:
        # Генерируем нечетное число
        candidate = random.randrange(2**(bits-1), 2**bits)
        if candidate % 2 == 0:
            candidate += 1
        
        if miller_rabin(candidate):
            return candidate

def extended_gcd(a, b):
    """Расширенный алгоритм Евклида"""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def mod_inverse(a, m):
    """Модульная инверсия"""
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError("Inverse doesn't exist")
    return (x % m + m) % m

class RSA:
    def __init__(self, key_size=2048):
        # Генерируем простые числа
        p = generate_prime(key_size // 2)
        q = generate_prime(key_size // 2)
        
        self.n = p * q
        φ = (p - 1) * (q - 1)
        
        # Стандартная экспонента
        self.e = 65537
        self.d = mod_inverse(self.e, φ)
        
        # Сохраняем для CRT оптимизации
        self.p = p
        self.q = q
        self.dp = self.d % (p - 1)
        self.dq = self.d % (q - 1)
        self.qinv = mod_inverse(q, p)
    
    def encrypt(self, m):
        """Шифрование: c = m^e mod n"""
        if m >= self.n:
            raise ValueError("Message too large")
        return pow(m, self.e, self.n)
    
    def decrypt(self, c):
        """Расшифрование с CRT оптимизацией"""
        # Используем CRT для ускорения
        mp = pow(c, self.dp, self.p)
        mq = pow(c, self.dq, self.q)
        
        # Объединяем результаты
        h = (self.qinv * (mp - mq)) % self.p
        m = mq + h * self.q
        return m
    
    def get_public_key(self):
        return (self.e, self.n)
    
    def get_private_key(self):
        return (self.d, self.n)

# Использование
rsa = RSA(key_size=1024)  # Для демо используем 1024 бит

# Шифрование
message = 12345
ciphertext = rsa.encrypt(message)
print(f"Encrypted: {ciphertext}")

# Расшифрование
decrypted = rsa.decrypt(ciphertext)
print(f"Decrypted: {decrypted}")
assert decrypted == message
```

**Оптимизации**:
1. **CRT** - ускоряет расшифрование в ~4 раза
2. **Малая экспонента** (65537) - быстрее шифрование
3. **Модульное возведение в степень** - использует бинарный метод
4. **Предвычисленные значения** (`dp`, `dq`, `qinv`) - для CRT

**Реальные библиотеки**: Используй `cryptography` или `pycryptodome` для production. Эта реализация только для обучения!

**Resources**:
- [Article] https://en.wikipedia.org/wiki/RSA_(cryptosystem) - RSA Wikipedia
- [Video] https://www.youtube.com/watch?v=wXB-V_Keiu8 - RSA объяснение
- [Article] https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/ - Python cryptography RSA
- [Code] https://github.com/pyca/cryptography - Реализация RSA в Python

**Related Concepts**: Модульная арифметика, Функция Эйлера, Китайская теорема об остатках, Тест простоты

---

## Concept: Модульная арифметика и группы
**Tags**: modular-arithmetic, group-theory, number-theory, discrete-math
**Estimated Time**: 25 minutes

### Level 1: Что такое модульная арифметика?
Объясни операции по модулю, классы вычетов, и основные свойства.

**Answer**:
Модульная арифметика - арифметика остатков от деления. Два числа эквивалентны по модулю `n`, если их разность делится на `n`.

**Определение**: `a ≡ b (mod n)` если `n | (a - b)`

**Основные операции**:
```python
# Сложение: (a + b) mod n
(17 + 23) % 12  # 4

# Умножение: (a * b) mod n
(17 * 23) % 12  # 7

# Возведение в степень: a^b mod n
pow(5, 3, 7)  # 6 (125 mod 7)

# Вычитание: (a - b) mod n
(5 - 8) % 7  # 4 (эквивалентно -3 mod 7)
```

**Свойства**:
- `(a + b) mod n = ((a mod n) + (b mod n)) mod n`
- `(a * b) mod n = ((a mod n) * (b mod n)) mod n`
- `a^b mod n = ((a mod n)^b) mod n`

**Классы вычетов**: Все числа, дающие одинаковый остаток, образуют класс:
- `[0] = {..., -12, 0, 12, 24, ...}` по модулю 12
- `[1] = {..., -11, 1, 13, 25, ...}` по модулю 12

### Level 2: Что такое мультипликативная группа по модулю?
Объясни группу Z_n*, обратимые элементы, и функцию Эйлера.

**Answer**:
Мультипликативная группа по модулю `n` - это множество чисел, взаимно простых с `n`, с операцией умножения.

**Z_n*** = {a: 1 ≤ a < n, gcd(a, n) = 1}

**Пример**: Z_12* = {1, 5, 7, 11} (все взаимно простые с 12)

```python
def multiplicative_group(n):
    """Возвращает мультипликативную группу по модулю n"""
    group = []
    for a in range(1, n):
        if math.gcd(a, n) == 1:
            group.append(a)
    return group

# Z_12* = [1, 5, 7, 11]
group = multiplicative_group(12)
print(group)  # [1, 5, 7, 11]

# Проверка групповых свойств
# Закрытость: 5 * 7 mod 12 = 35 mod 12 = 11 (в группе)
# Ассоциативность: (5 * 7) * 11 = 5 * (7 * 11) mod 12
# Единица: 1 (любой элемент * 1 = сам элемент)
# Обратный: 5 * 5 = 25 mod 12 = 1, значит 5 обратен сам себе
```

**Функция Эйлера φ(n)**:
Количество чисел от 1 до n, взаимно простых с n. Равна размеру группы Z_n*.

```python
def euler_phi(n):
    """Вычисляет φ(n) - функцию Эйлера"""
    count = 0
    for i in range(1, n + 1):
        if math.gcd(i, n) == 1:
            count += 1
    return count

# Для простого p: φ(p) = p - 1
assert euler_phi(7) == 6

# Для произведения простых p*q: φ(p*q) = (p-1)(q-1)
assert euler_phi(12) == 4  # φ(12) = φ(4)*φ(3) = 2*2 = 4
```

**Теорема Эйлера**: Если `gcd(a, n) = 1`, то `a^φ(n) ≡ 1 (mod n)`

**Малая теорема Ферма**: Если `p` простое и `gcd(a, p) = 1`, то `a^(p-1) ≡ 1 (mod p)`

```python
# Проверка теоремы Эйлера
a, n = 5, 12
assert math.gcd(a, n) == 1
phi_n = euler_phi(n)  # 4
assert pow(a, phi_n, n) == 1  # 5^4 mod 12 = 1
```

### Level 3: Дискретное логарифмирование и генераторы
Объясни дискретный логарифм, генераторы группы, и их применение в криптографии.

**Answer**:
Дискретный логарифм - обратная операция к возведению в степень в группе.

**Определение**: Если `g^x ≡ h (mod n)`, то `x = log_g(h) mod n`

**Пример**:
```python
# В группе Z_11* = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
g = 2
h = 8

# Найти x такой, что 2^x ≡ 8 (mod 11)
for x in range(1, 11):
    if pow(g, x, 11) == h:
        print(f"log_2(8) = {x} mod 11")  # 3
        break
```

**Генератор группы**:
Элемент `g`, степени которого порождают всю группу. Если `g` генератор Z_n*, то {g^1, g^2, ..., g^φ(n)} = Z_n*

```python
def is_generator(g, n):
    """Проверяет, является ли g генератором Z_n*"""
    phi = euler_phi(n)
    powers = set()
    for i in range(1, phi + 1):
        power = pow(g, i, n)
        if power in powers:
            return False  # Повторение - не генератор
        powers.add(power)
    return len(powers) == phi

# Проверка генераторов Z_11*
for g in range(2, 11):
    if is_generator(g, 11):
        print(f"{g} is a generator of Z_11*")
# Вывод: 2, 6, 7, 8 - генераторы
```

**Применение в криптографии**:
- **Diffie-Hellman**: Обмен ключами основан на сложности дискретного логарифма
- **ElGamal**: Шифрование использует дискретный логарифм
- **DSA/ECDSA**: Подписи используют дискретный логарифм

**Сложность**: Для больших групп дискретный логарифм вычислительно сложен (основа безопасности).

### Level 4: Китайская теорема об остатках (CRT)
Объясни CRT, как она ускоряет вычисления в RSA, и алгоритм решения системы сравнений.

**Answer**:
CRT позволяет решать системы сравнений и ускоряет вычисления в RSA.

**Формулировка**: Если `n_1, n_2, ..., n_k` попарно взаимно просты, то система:
```
x ≡ a_1 (mod n_1)
x ≡ a_2 (mod n_2)
...
x ≡ a_k (mod n_k)
```
имеет единственное решение по модулю `N = n_1 * n_2 * ... * n_k`.

**Алгоритм решения**:
```python
def chinese_remainder_theorem(remainders, moduli):
    """Решает систему сравнений через CRT"""
    N = 1
    for n in moduli:
        N *= n
    
    result = 0
    for i, (a_i, n_i) in enumerate(zip(remainders, moduli)):
        N_i = N // n_i
        # Находим обратный к N_i по модулю n_i
        _, inv, _ = extended_gcd(N_i, n_i)
        result += a_i * N_i * inv
    
    return result % N

# Пример: найти x такой, что
# x ≡ 2 (mod 3)
# x ≡ 3 (mod 5)
# x ≡ 2 (mod 7)
x = chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
print(x)  # 23
assert x % 3 == 2 and x % 5 == 3 and x % 7 == 2
```

**Применение в RSA**:
Вместо вычисления `m^d mod n` (где `n = p * q`), вычисляем:
- `m_p = m^d mod p`
- `m_q = m^d mod q`
- Объединяем через CRT

```python
def rsa_decrypt_crt(c, d, p, q):
    """Быстрое расшифрование RSA через CRT"""
    n = p * q
    
    # Вычисляем по модулям p и q (быстрее!)
    dp = d % (p - 1)
    dq = d % (q - 1)
    mp = pow(c, dp, p)
    mq = pow(c, dq, q)
    
    # Объединяем через CRT
    # x ≡ mp (mod p), x ≡ mq (mod q)
    qinv = mod_inverse(q, p)
    h = (qinv * (mp - mq)) % p
    m = mq + h * q
    
    return m % n

# Ускорение в ~4 раза по сравнению с прямым вычислением
```

**Почему быстрее**: Возведение в степень по модулю `p` и `q` (малые числа) быстрее, чем по модулю `n = p*q` (большое число).

**Resources**:
- [Article] https://en.wikipedia.org/wiki/Modular_arithmetic - Модульная арифметика
- [Article] https://en.wikipedia.org/wiki/Euler%27s_totient_function - Функция Эйлера
- [Video] https://www.youtube.com/watch?v=ru7mWZJlRQg - Китайская теорема об остатках
- [Article] https://en.wikipedia.org/wiki/Discrete_logarithm - Дискретное логарифмирование

**Related Concepts**: RSA, Группы, Кольца, Поля, Теорема Эйлера

---

## Concept: Алгебраические структуры
**Tags**: abstract-algebra, groups, rings, fields, number-theory
**Estimated Time**: 20 minutes

### Level 1: Что такое группы, кольца и поля?
Объясни основные алгебраические структуры и их свойства.

**Answer**:
Алгебраические структуры определяют операции и их свойства.

**Группа (G, *)**:
Множество с бинарной операцией, удовлетворяющей:
1. **Закрытость**: `a * b ∈ G` для всех `a, b ∈ G`
2. **Ассоциативность**: `(a * b) * c = a * (b * c)`
3. **Единица**: Существует `e` такой, что `e * a = a * e = a`
4. **Обратный**: Для каждого `a` существует `a^(-1)` такой, что `a * a^(-1) = e`

**Пример**: Z_n* (мультипликативная группа по модулю n)

**Кольцо (R, +, *)**:
Множество с двумя операциями:
- (R, +) - абелева группа
- Умножение ассоциативно и дистрибутивно: `a * (b + c) = a*b + a*c`

**Пример**: Z_n (кольцо вычетов по модулю n)

**Поле (F, +, *)**:
Кольцо, где (F\{0}, *) - абелева группа (все ненулевые элементы обратимы).

**Пример**: Z_p где p простое (конечное поле)

```python
# Пример поля Z_7
def is_field(n):
    """Проверяет, является ли Z_n полем"""
    if n < 2:
        return False
    # Z_n - поле тогда и только тогда, когда n простое
    return miller_rabin(n, k=10)

assert is_field(7)  # True - простое
assert not is_field(12)  # False - составное
```

### Level 2: Конечные поля и их применение
Объясни конечные поля GF(p) и GF(2^n), и их использование в криптографии.

**Answer**:
Конечные поля (поля Галуа) - поля с конечным числом элементов.

**GF(p)** - поле простого порядка:
- Элементы: {0, 1, 2, ..., p-1}
- Сложение и умножение по модулю p
- Все ненулевые элементы обратимы

**GF(2^n)** - поле степени 2:
- Элементы - многочлены степени < n над GF(2)
- Сложение - XOR
- Умножение - умножение многочленов по модулю неприводимого многочлена

```python
# GF(7) - простое поле
class GFp:
    def __init__(self, value, p):
        self.value = value % p
        self.p = p
    
    def __add__(self, other):
        return GFp(self.value + other.value, self.p)
    
    def __mul__(self, other):
        return GFp(self.value * other.value, self.p)
    
    def __pow__(self, exp):
        return GFp(pow(self.value, exp, self.p), self.p)
    
    def inverse(self):
        return GFp(mod_inverse(self.value, self.p), self.p)

# Использование
a = GFp(3, 7)
b = GFp(5, 7)
print((a + b).value)  # 1 (3+5 mod 7)
print((a * b).value)  # 1 (3*5 mod 7)
print((a ** 6).value)  # 1 (теорема Ферма: 3^6 mod 7 = 1)
```

**Применение**:
- **AES**: Использует GF(2^8) для операций в S-box
- **Elliptic Curve Cryptography**: Кривые над конечными полями
- **Reed-Solomon codes**: Коды исправления ошибок

**Resources**:
- [Article] https://en.wikipedia.org/wiki/Finite_field - Конечные поля
- [Video] https://www.youtube.com/watch?v=z9bTzjy4SCg - Группы, кольца, поля
- [Article] https://en.wikipedia.org/wiki/Galois_field - Поля Галуа

**Related Concepts**: Модульная арифметика, RSA, Elliptic Curves, Кодирование

