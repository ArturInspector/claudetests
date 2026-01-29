#!/bin/bash

set -e

SESSIONS_DIR="sessions"
TEMPLATES_DIR="templates"

cmd_start() {
    local topic="$1"
    if [ -z "$topic" ]; then
        echo "Usage: ./learn.sh start \"Topic Name\""
        exit 1
    fi
    
    local slug=$(echo "$topic" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local session_dir="$SESSIONS_DIR/$slug"
    
    mkdir -p "$session_dir"
    
    cat > "$session_dir/iteration-1.md" <<EOF
# Learning Session: $topic

**Date**: $(date +%Y-%m-%d)
**Iteration**: 1
**Level**: [junior/middle/senior]

## Questions

### Q1: Базовое понимание
Объясни концепт "$topic" своими словами.

**Твой ответ:**


---

### Q2: Компоненты
Какие ключевые элементы составляют "$topic"?

**Твой ответ:**


---

### Q3: Проблема
Какую проблему решает "$topic"?

**Твой ответ:**


---

### Q4: Альтернативы
Какие есть альтернативы или смежные концепты?

**Твой ответ:**


---

### Q5: Trade-offs
Какие есть ограничения или компромиссы?

**Твой ответ:**


---

### Q6: Real-world
Приведи пример использования в реальных системах.

**Твой ответ:**


---

### Q7: Технические детали
Объясни технические аспекты имплементации.

**Твой ответ:**


---

### Q8: Edge cases
Какие edge cases нужно учитывать?

**Твой ответ:**


---

### Q9: Интеграция
Как "$topic" интегрируется с другими системами?

**Твой ответ:**


---

### Q10: Практика
Спроектируй систему, использующую "$topic".

**Твой ответ:**


---

## После ответов запусти: ./learn.sh analyze sessions/$slug/iteration-1.md
EOF
    
    echo "✅ Created: $session_dir/iteration-1.md"
    echo "📝 Fill your answers, then run: ./learn.sh analyze $session_dir/iteration-1.md"
}

cmd_analyze() {
    local file="$1"
    if [ -z "$file" ] || [ ! -f "$file" ]; then
        echo "Usage: ./learn.sh analyze sessions/topic/iteration-1.md"
        exit 1
    fi
    
    echo "🤖 Analyzing with Claude..."
    echo ""
    echo "PROMPT FOR CLAUDE:"
    echo "────────────────────────────────────────"
    cat <<EOF
Проанализируй мои ответы в файле: $file

Оцени по критериям:
1. **Глубина понимания** (не правильность!)
2. **Gaps** - что я не понимаю или упускаю
3. **Strong areas** - где понимание хорошее

Формат ответа:
\`\`\`json
{
  "understood": ["концепт 1", "концепт 2"],
  "needsWork": [
    {
      "area": "partition tolerance",
      "reason": "поверхностное понимание, нет примеров"
    }
  ],
  "recommendations": [
    "Изучи как partition tolerance работает в Ethereum",
    "Прочитай про network partitions в Byzantine systems"
  ],
  "nextFocus": "partition tolerance + consensus algorithms"
}
\`\`\`
EOF
    echo "────────────────────────────────────────"
    echo ""
    echo "💡 Copy file content and prompt to Claude, then save analysis to:"
    echo "   ${file%/*}/analysis.json"
}

cmd_next() {
    local file="$1"
    if [ -z "$file" ]; then
        echo "Usage: ./learn.sh next sessions/topic/iteration-1.md"
        exit 1
    fi
    
    local dir=$(dirname "$file")
    local current_iter=$(basename "$file" | grep -oP '\d+')
    local next_iter=$((current_iter + 1))
    local analysis="$dir/analysis.json"
    
    if [ ! -f "$analysis" ]; then
        echo "❌ Run './learn.sh analyze $file' first"
        exit 1
    fi
    
    echo "🤖 Generating iteration $next_iter..."
    echo ""
    echo "PROMPT FOR CLAUDE:"
    echo "────────────────────────────────────────"
    cat <<EOF
На основе analysis.json создай iteration-$next_iter.md

Фокус на areas from needsWork. Генерируй:
- 5-7 глубоких вопросов на слабые зоны
- Практические задачи
- Code examples если применимо

Формат:
# Learning Session: [Topic] - Iteration $next_iter

## Focus Areas
[List from needsWork]

## Deep-Dive Questions
[Targeted questions]

## Практические задачи
[Hands-on tasks]
EOF
    echo "────────────────────────────────────────"
    echo ""
    echo "💾 Save result to: $dir/iteration-$next_iter.md"
}

cmd_help() {
    cat <<EOF
Socratic Learning CLI

Commands:
  start "Topic"           Start new learning session
  analyze <file>          Analyze answers, generate gaps
  next <file>            Generate next iteration

Examples:
  ./learn.sh start "CAP theorem"
  ./learn.sh analyze sessions/cap-theorem/iteration-1.md
  ./learn.sh next sessions/cap-theorem/iteration-1.md
EOF
}

# Main
case "${1:-}" in
    start) cmd_start "$2" ;;
    analyze) cmd_analyze "$2" ;;
    next) cmd_next "$2" ;;
    *) cmd_help ;;
esac

