import re
from typing import List, Dict, Optional


class QuestionParser:
    """Парсер .md файлов с вопросами для импорта в базу данных"""
    
    def __init__(self, content: str):
        self.content = content
        self.topic_name = None
        self.questions = []
    
    def parse(self) -> Dict:
        """Парсит весь файл и возвращает структуру с темой и вопросами"""
        self._extract_topic()
        self._extract_questions()
        
        return {
            "topic": self.topic_name,
            "questions": self.questions
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
    
    def _extract_questions(self):
        """Извлекает все вопросы из файла"""
        # Разделяем по ## Question: или просто по ---
        question_blocks = re.split(r'(?=^## Question:|^---$)', self.content, flags=re.MULTILINE)
        
        for block in question_blocks:
            block = block.strip()
            if not block or block.startswith('# Topic:') or block == '---':
                continue
            
            question = self._parse_question_block(block)
            if question:
                self.questions.append(question)
    
    def _parse_question_block(self, block: str) -> Optional[Dict]:
        """Парсит один блок вопроса"""
        # Извлекаем заголовок вопроса
        title_match = re.search(r'## Question:\s+(.+?)(?:\n|$)', block)
        if not title_match:
            return None
        
        title = title_match.group(1).strip()
        
        # Извлекаем сложность (difficulty)
        difficulty_match = re.search(r'\*\*Difficulty\*\*:\s*(\w+)', block, re.IGNORECASE)
        difficulty = difficulty_match.group(1) if difficulty_match else "Medium"
        
        # Извлекаем тип (type)
        type_match = re.search(r'\*\*Type\*\*:\s*(\w+)', block, re.IGNORECASE)
        question_type = type_match.group(1) if type_match else "Text"
        
        # Разделяем на вопрос и ответ по **Answer**:
        parts = re.split(r'\*\*Answer\*\*:', block, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return None
        
        # Текст вопроса (все между метаданными и **Answer**)
        question_text = parts[0]
        
        # Убираем заголовок и метаданные из текста вопроса
        question_text = re.sub(r'## Question:.+?\n', '', question_text)
        question_text = re.sub(r'\*\*Difficulty\*\*:.+?\n', '', question_text, flags=re.IGNORECASE)
        question_text = re.sub(r'\*\*Type\*\*:.+?\n', '', question_text, flags=re.IGNORECASE)
        question_text = question_text.strip()
        
        # Текст ответа
        answer_text = parts[1].strip()
        
        return {
            "title": title,
            "difficulty": difficulty,
            "question_type": question_type,
            "question_text": question_text,
            "answer_text": answer_text
        }


def parse_markdown_file(file_path: str) -> Dict:
    """Читает и парсит .md файл с вопросами"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = QuestionParser(content)
    return parser.parse()


def parse_markdown_content(content: str) -> Dict:
    """Парсит содержимое markdown напрямую (для загрузки через API)"""
    parser = QuestionParser(content)
    return parser.parse()


if __name__ == "__main__":
    # Пример для тестирования
    test_content = """# Topic: Solidity Advanced

## Question: Reentrancy Attack
**Difficulty**: Medium
**Type**: Code

Что не так с этим кодом?
```solidity
function withdraw() public {
    uint amount = balances[msg.sender];
    msg.sender.call{value: amount}("");
    balances[msg.sender] = 0;
}
```

**Answer**:
Reentrancy уязвимость. Нужно обновлять balance до отправки:
```solidity
balances[msg.sender] = 0;
msg.sender.call{value: amount}("");
```
Или использовать ReentrancyGuard от OpenZeppelin.

---

## Question: Gas Optimization
**Difficulty**: Hard
**Type**: Code

Как оптимизировать этот код?
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
1. Кэшировать values.length
2. Использовать unchecked для i++
3. Кэшировать values[i] в memory переменную
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
"""
    
    parser = QuestionParser(test_content)
    result = parser.parse()
    
    print(f"Topic: {result['topic']}")
    print(f"Questions found: {len(result['questions'])}")
    for q in result['questions']:
        print(f"\n- {q['title']} ({q['difficulty']}, {q['question_type']})")

