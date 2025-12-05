"""
Парсер для задач из Markdown файлов
Формат задач отличается от вопросов - здесь нужен starter code и тесты
"""
import re
from typing import List, Dict, Optional


class TaskParser:
    """Парсер .md файлов с задачами для импорта в базу данных"""
    
    def __init__(self, content: str):
        self.content = content
        self.topic_name = None
        self.tasks = []
    
    def parse(self) -> Dict:
        """Парсит весь файл и возвращает структуру с темой и задачами"""
        self._extract_topic()
        self._extract_tasks()
        
        return {
            "topic": self.topic_name,
            "tasks": self.tasks
        }
    
    def _extract_topic(self):
        """Извлекает название темы из первого заголовка # Topic: ..."""
        topic_match = re.search(r'^#\s+Topic:\s+(.+)$', self.content, re.MULTILINE)
        if topic_match:
            self.topic_name = topic_match.group(1).strip()
        else:
            # Если нет специального заголовка, берем первый H1
            h1_match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
            self.topic_name = h1_match.group(1).strip() if h1_match else "General"
    
    def _extract_tasks(self):
        """Извлекает задачи из файла"""
        # Разделяем по ## Task: или ## Задача:
        task_blocks = re.split(r'(?=^##\s+(?:Task|Задача):)', self.content, flags=re.MULTILINE | re.IGNORECASE)
        
        for block in task_blocks:
            block = block.strip()
            if not block or block.startswith('# Topic:'):
                continue
            
            task = self._parse_task_block(block)
            if task:
                self.tasks.append(task)
    
    def _parse_task_block(self, block: str) -> Optional[Dict]:
        """Парсит один блок задачи"""
        # Извлекаем название задачи
        title_match = re.search(r'##\s+(?:Task|Задача):\s+(.+?)(?:\n|$)', block, re.IGNORECASE)
        if not title_match:
            return None
        
        title = title_match.group(1).strip()
        
        # Извлекаем метаданные
        difficulty_match = re.search(r'\*\*Difficulty\*\*:\s*(\w+)', block, re.IGNORECASE)
        difficulty = difficulty_match.group(1) if difficulty_match else "Medium"
        
        language_match = re.search(r'\*\*Language\*\*:\s*(\w+)', block, re.IGNORECASE)
        language = language_match.group(1).lower() if language_match else "go"
        
        time_match = re.search(r'\*\*Estimated Time\*\*:\s*(\d+)\s*(?:min|minutes|мин)', block, re.IGNORECASE)
        estimated_time = int(time_match.group(1)) if time_match else None
        
        order_match = re.search(r'\*\*Order\*\*:\s*(\d+)', block, re.IGNORECASE)
        order = int(order_match.group(1)) if order_match else 0
        
        # Извлекаем описание
        description_match = re.search(r'\*\*Description\*\*:\s*(.+?)(?=\*\*|```|##|$)', block, re.DOTALL | re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else ""
        
        # Определяем тип задачи (write или review)
        task_type_match = re.search(r'\*\*Type\*\*:\s*(\w+)', block, re.IGNORECASE)
        task_type = task_type_match.group(1).lower() if task_type_match else "write"
        
        # Определяем блок (write или review)
        block_match = re.search(r'\*\*Block\*\*:\s*(\w+)', block, re.IGNORECASE)
        block_type = block_match.group(1).lower() if block_match else ("write" if task_type == "write" else "review")
        
        # Извлекаем требования
        requirements = self._extract_section(block, r'\*\*Requirements?\*\*:', r'\*\*|```|##')
        
        # Извлекаем теги
        tags_match = re.search(r'\*\*Tags?\*\*:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        tags = None
        if tags_match:
            tags_str = tags_match.group(1).strip()
            tags = [t.strip() for t in tags_str.split(',')]
        
        result = {
            "title": title,
            "description": description,
            "task_type": task_type,
            "block": block_type,
            "difficulty": difficulty,
            "language": language,
            "estimated_time": estimated_time,
            "requirements": requirements,
            "tags": tags,
            "order": order
        }
        
        if task_type == "review":
            # Для Review задач
            ai_code = self._extract_code_block(block, "AI Code", "ai")
            if not ai_code:
                ai_code = self._extract_code_block(block, "Code", "code")
            
            review_questions = self._extract_list(block, r'\*\*Review Questions?\*\*:', r'\*\*|```|##')
            if not review_questions:
                review_questions = self._extract_list(block, r'\*\*Questions?\*\*:', r'\*\*|```|##')
            
            expected_issues = self._extract_list(block, r'\*\*Expected Issues?\*\*:', r'\*\*|```|##')
            
            if not ai_code:
                return None
            
            result.update({
                "ai_code": ai_code,
                "review_questions": review_questions,
                "expected_issues": expected_issues,
                "starter_code": None,
                "test_code": None,
                "solution_code": None,
                "hints": None
            })
        else:
            # Для Write задач
            starter_code = self._extract_code_block(block, "Starter Code", "starter")
            if not starter_code:
                starter_code = self._extract_code_block(block, "Код", "code")
            
            test_code = self._extract_code_block(block, "Tests", "test")
            if not test_code:
                test_code = self._extract_code_block(block, "Тесты", "test")
            
            solution_code = self._extract_code_block(block, "Solution", "solution")
            if not solution_code:
                solution_code = self._extract_code_block(block, "Решение", "solution")
            
            hints = self._extract_list(block, r'\*\*Hints?\*\*:', r'\*\*|```|##')
            if not hints:
                hints = self._extract_list(block, r'\*\*Подсказки?\*\*:', r'\*\*|```|##')
            
            if not starter_code:
                return None
            
            result.update({
                "starter_code": starter_code,
                "test_code": test_code,
                "solution_code": solution_code,
                "hints": hints,
                "ai_code": None,
                "review_questions": None,
                "expected_issues": None
            })
        
        return result
    
    def _extract_code_block(self, block: str, section_name: str, fallback_pattern: str = None) -> Optional[str]:
        """Извлекает код из блока с определенным названием секции"""
        # Ищем секцию по названию
        section_pattern = rf'\*\*{section_name}\*\*:\s*\n(.*?)(?=\*\*|```|##|$)'
        section_match = re.search(section_pattern, block, re.DOTALL | re.IGNORECASE)
        
        if section_match:
            section_content = section_match.group(1)
            # Ищем код в этой секции
            code_match = re.search(r'```(?:\w+)?\n(.*?)```', section_content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
        
        # Fallback: ищем любой код блок после упоминания секции
        if fallback_pattern:
            pattern = rf'{fallback_pattern}.*?```(?:\w+)?\n(.*?)```'
            code_match = re.search(pattern, block, re.DOTALL | re.IGNORECASE)
            if code_match:
                return code_match.group(1).strip()
        
        return None
    
    def _extract_section(self, block: str, pattern: str, end_pattern: str) -> Optional[str]:
        """Извлекает текстовую секцию"""
        match = re.search(pattern + r'\s*(.+?)(?=' + end_pattern + r'|$)', block, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            # Убираем код блоки из текста
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            return text.strip()
        return None
    
    def _extract_list(self, block: str, pattern: str, end_pattern: str) -> Optional[List[str]]:
        """Извлекает список элементов"""
        section = self._extract_section(block, pattern, end_pattern)
        if not section:
            return None
        
        # Разделяем по строкам или маркерам списка
        items = []
        for line in section.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Убираем маркеры списка (-, *, 1., etc.)
            line = re.sub(r'^[-*•]\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line)
            
            if line:
                items.append(line)
        
        return items if items else None


def parse_task_markdown(content: str) -> Dict:
    """Парсит содержимое markdown с задачами"""
    parser = TaskParser(content)
    return parser.parse()


if __name__ == "__main__":
    # Пример для тестирования
    test_content = """# Topic: Go Basics

## Task: HTTP Server
**Difficulty**: Easy
**Language**: Go
**Estimated Time**: 30 min
**Order**: 1

**Description**:
Создай простой HTTP сервер который отвечает "Hello World" на GET /hello

**Requirements**:
- Используй только стандартную библиотеку Go
- Сервер должен слушать на порту 8080
- Обработчик должен быть функцией

**Starter Code**:
```go
package main

import (
    "fmt"
    "net/http"
)

func main() {
    // TODO: добавь HTTP handler
    // TODO: запусти сервер на порту 8080
}
```

**Tests**:
```go
package main

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestHelloHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/hello", nil)
    w := httptest.NewRecorder()
    
    helloHandler(w, req)
    
    if w.Code != http.StatusOK {
        t.Errorf("Expected status 200, got %d", w.Code)
    }
    
    if w.Body.String() != "Hello World" {
        t.Errorf("Expected 'Hello World', got '%s'", w.Body.String())
    }
}
```

**Hints**:
- Используй http.HandleFunc для регистрации handler
- http.ListenAndServe запускает сервер
- Handler функция принимает (http.ResponseWriter, *http.Request)
"""
    
    parser = TaskParser(test_content)
    result = parser.parse()
    
    print(f"Topic: {result['topic']}")
    print(f"Tasks found: {len(result['tasks'])}")
    for task in result['tasks']:
        print(f"\n- {task['title']}")
        print(f"  Language: {task['language']}")
        print(f"  Difficulty: {task['difficulty']}")
        print(f"  Has starter code: {bool(task['starter_code'])}")
        print(f"  Has tests: {bool(task['test_code'])}")

