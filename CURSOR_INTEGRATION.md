# Cursor Integration

## Как использовать с Cursor

### 1. Workflow в Cursor
```
1. Открываешь session MD в редакторе
2. Заполняешь ответы
3. В чате: "Проанализируй мои ответы в iteration-1.md"
4. Claude читает файл, генерит analysis
5. Сохраняешь analysis.json
6. В чате: "Создай следующую итерацию"
```

### 2. Prompt Templates

#### Анализ ответов
```
Проанализируй мои ответы в [file]. Оцени глубину понимания, найди gaps.
Формат: JSON как в templates/analysis-template.json
```

#### Генерация следующей итерации
```
На основе analysis.json создай iteration-N.md.
Фокус на needsWork areas. 5-7 глубоких вопросов + практические задачи.
```

#### Code review с CAP контекстом
```
Review этот код с точки зрения CAP theorem:
[код]

Какие CAP trade-offs? Edge cases при network partition?
```

### 3. Автоматизация через Rules

Добавь в `.cursorrules`:
```
Когда пользователь работает с файлами в sessions/:
1. Автоматически подтягивай прошлые iterations для контекста
2. При анализе ответов - используй формат из templates/analysis-template.json
3. При генерации вопросов - фокусируйся на gaps из последнего analysis.json
4. Для blockchain тем - всегда связывай с real-world примерами (Ethereum, Bitcoin, Hyperledger)
```

### 4. Keyboard shortcuts

Добавь в Cursor:
```json
{
  "key": "cmd+shift+a",
  "command": "workbench.action.chat.open",
  "args": "Проанализируй текущий session file"
}
```

### 5. Multi-file context

Claude в Cursor видит:
- Текущий iteration файл
- analysis.json из той же папки
- Прошлые iterations для tracking прогресса

Используй:
```
@sessions/cap-theorem Создай iteration-3 на основе всей истории
```

## Best Practices

1. **Один session = одна тема** - не смешивай CAP и другие темы
2. **Commit после каждой iteration** - видно эволюцию понимания
3. **Используй @-mentions** - `@iteration-1.md` для контекста
4. **Practical код примеры** - всегда прошу Claude давать runnable code
5. **Export в Obsidian** - `sessions/` папка = Obsidian vault

