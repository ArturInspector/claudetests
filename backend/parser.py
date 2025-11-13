import re
from typing import List, Dict, Optional


class QuestionParser:
    """Парсер .md файлов с вопросами для импорта в базу данных
    
    Поддерживает:
    - Одиночные вопросы (старый формат)
    - Многоуровневые концепты (Concept → Level 1-4)
    - Tags, Estimated Time
    - Resources
    - Related Concepts
    """
    
    def __init__(self, content: str):
        self.content = content
        self.topic_name = None
        self.questions = []
        self.resources = []
        self.concept_links = []
    
    def parse(self) -> Dict:
        """Парсит весь файл и возвращает структуру с темой и вопросами"""
        self._extract_topic()
        self._extract_concepts_and_questions()
        
        return {
            "topic": self.topic_name,
            "questions": self.questions,
            "resources": self.resources,
            "concept_links": self.concept_links
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
    
    def _extract_concepts_and_questions(self):
        """Извлекает концепты и вопросы (поддержка обоих форматов)"""
        # Проверяем наличие ## Concept: (новый формат)
        if '## Concept:' in self.content:
            self._extract_multi_level_concepts()
        else:
            # Старый формат - простые вопросы
            self._extract_simple_questions()
    
    def _extract_simple_questions(self):
        """Извлекает простые вопросы (старый формат)"""
        question_blocks = re.split(r'(?=^## Question:|^---$)', self.content, flags=re.MULTILINE)
        
        for block in question_blocks:
            block = block.strip()
            if not block or block.startswith('# Topic:') or block == '---':
                continue
            
            question = self._parse_simple_question(block)
            if question:
                self.questions.append(question)
    
    def _parse_simple_question(self, block: str) -> Optional[Dict]:
        """Парсит один простой вопрос"""
        title_match = re.search(r'## Question:\s+(.+?)(?:\n|$)', block)
        if not title_match:
            return None
        
        title = title_match.group(1).strip()
        
        # Извлекаем метаданные
        difficulty_match = re.search(r'\*\*Difficulty\*\*:\s*(\w+)', block, re.IGNORECASE)
        difficulty = difficulty_match.group(1) if difficulty_match else "Medium"
        
        type_match = re.search(r'\*\*Type\*\*:\s*(\w+)', block, re.IGNORECASE)
        question_type = type_match.group(1) if type_match else "Text"
        
        # Разделяем на вопрос и ответ
        parts = re.split(r'\*\*Answer\*\*:', block, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return None
        
        question_text = parts[0]
        question_text = re.sub(r'## Question:.+?\n', '', question_text)
        question_text = re.sub(r'\*\*Difficulty\*\*:.+?\n', '', question_text, flags=re.IGNORECASE)
        question_text = re.sub(r'\*\*Type\*\*:.+?\n', '', question_text, flags=re.IGNORECASE)
        question_text = question_text.strip()
        
        answer_text = parts[1].strip()
        
        return {
            "title": title,
            "difficulty": difficulty,
            "question_type": question_type,
            "question_text": question_text,
            "answer_text": answer_text,
            "level": 1,
            "parent_concept_id": None,
            "tags": None,
            "estimated_time": None
        }
    
    def _extract_multi_level_concepts(self):
        """Извлекает многоуровневые концепты"""
        # Разделяем по ## Concept:
        concept_blocks = re.split(r'(?=^## Concept:)', self.content, flags=re.MULTILINE)
        
        for block in concept_blocks:
            block = block.strip()
            if not block or block.startswith('# Topic:'):
                continue
            
            self._parse_concept_block(block)
    
    def _parse_concept_block(self, block: str):
        """Парсит один концепт с подуровнями"""
        # Извлекаем название концепта
        concept_match = re.search(r'## Concept:\s+(.+?)(?:\n|$)', block)
        if not concept_match:
            return
        
        concept_name = concept_match.group(1).strip()
        
        # Извлекаем метаданные концепта
        tags = self._extract_tags(block)
        estimated_time = self._extract_estimated_time(block)
        
        # Извлекаем resources
        resources = self._extract_resources(block, concept_name)
        self.resources.extend(resources)
        
        # Извлекаем related concepts
        related = self._extract_related_concepts(block, concept_name)
        self.concept_links.extend(related)
        
        # Извлекаем levels (### Level 1:, ### Level 2:, etc.)
        level_blocks = re.findall(r'### Level (\d+):\s+(.+?)\n(.*?)(?=### Level \d+:|$)', block, re.DOTALL)
        
        parent_question_id = None
        
        for level_num, level_title, level_content in level_blocks:
            level = int(level_num)
            
            # Разделяем на вопрос и ответ
            parts = re.split(r'\*\*Answer\*\*:', level_content, flags=re.IGNORECASE)
            
            if len(parts) < 2:
                continue
            
            question_text = parts[0].strip()
            answer_text = parts[1].strip()
            
            # Определяем difficulty на основе level
            difficulty = self._level_to_difficulty(level)
            
            question = {
                "title": f"{concept_name} - {level_title}",
                "difficulty": difficulty,
                "question_type": "Text",  # По умолчанию, можно расширить
                "question_text": question_text,
                "answer_text": answer_text,
                "level": level,
                "parent_concept_id": parent_question_id,  # Первый уровень - parent
                "tags": tags,
                "estimated_time": estimated_time if level == 1 else None
            }
            
            self.questions.append(question)
            
            # Первый level становится parent для остальных
            if level == 1:
                parent_question_id = len(self.questions) - 1  # Временный ID
    
    def _extract_tags(self, block: str) -> Optional[List[str]]:
        """Извлекает tags из блока"""
        tags_match = re.search(r'\*\*Tags\*\*:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            # Разделяем по запятой и очищаем
            tags = [t.strip() for t in tags_str.split(',')]
            return tags
        return None
    
    def _extract_estimated_time(self, block: str) -> Optional[int]:
        """Извлекает estimated time в минутах"""
        time_match = re.search(r'\*\*Estimated Time\*\*:\s*(\d+)\s*min', block, re.IGNORECASE)
        if time_match:
            return int(time_match.group(1))
        return None
    
    def _extract_resources(self, block: str, concept_name: str) -> List[Dict]:
        """Извлекает ресурсы из блока"""
        resources = []
        
        # Ищем секцию **Resources**:
        resources_match = re.search(r'\*\*Resources\*\*:(.*?)(?=\*\*[A-Z]|###|##|$)', block, re.DOTALL | re.IGNORECASE)
        if not resources_match:
            return resources
        
        resources_text = resources_match.group(1)
        
        # Парсим каждый ресурс: - [Type] URL - Title
        resource_lines = re.findall(r'-\s*\[(\w+)\]\s+(.+?)\s+-\s+(.+?)(?:\n|$)', resources_text)
        
        for res_type, url, title in resource_lines:
            resources.append({
                "type": res_type.lower(),
                "url": url.strip(),
                "title": title.strip(),
                "concept_name": concept_name
            })
        
        return resources
    
    def _extract_related_concepts(self, block: str, concept_name: str) -> List[Dict]:
        """Извлекает связанные концепты"""
        related = []
        
        related_match = re.search(r'\*\*Related Concepts\*\*:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if related_match:
            related_str = related_match.group(1).strip()
            # Разделяем по запятой
            related_names = [r.strip() for r in related_str.split(',')]
            
            for rel_name in related_names:
                related.append({
                    "from_concept": concept_name,
                    "to_concept": rel_name,
                    "relationship_type": "related"
                })
        
        return related
    
    def _level_to_difficulty(self, level: int) -> str:
        """Конвертирует level в difficulty"""
        if level == 1:
            return "Easy"
        elif level == 2:
            return "Medium"
        elif level in [3, 4]:
            return "Hard"
        return "Medium"


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
    # Пример для тестирования нового формата
    test_content = """# Topic: Solidity Advanced

## Concept: Reentrancy Attacks
**Tags**: security, vulnerabilities, CEI-pattern
**Estimated Time**: 20 minutes

### Level 1: What is reentrancy?
Объясни что такое reentrancy attack в Solidity.

**Answer**:
Reentrancy - это уязвимость когда внешний контракт может повторно вызвать функцию до завершения первого вызова.

### Level 2: How does CEI pattern help?
Как Checks-Effects-Interactions pattern защищает от reentrancy?

**Answer**:
CEI pattern предписывает порядок: 1) Проверки, 2) Изменение state, 3) Внешние вызовы. Это предотвращает reentrancy.

### Level 3: Cross-contract reentrancy
Объясни cross-contract reentrancy и как от него защититься.

**Answer**:
Cross-contract reentrancy происходит когда состояние разделяется между контрактами. Защита - глобальные locks или ReentrancyGuard.

**Resources**:
- [Video] https://youtube.com/watch?v=abc - Smart Contract Programmer Tutorial
- [Article] https://consensys.net/security - Best Practices Guide
- [Code] https://github.com/OpenZeppelin/openzeppelin-contracts - ReentrancyGuard Implementation

**Related Concepts**: CEI Pattern, State Mutations, Gas Optimization
"""
    
    parser = QuestionParser(test_content)
    result = parser.parse()
    
    print(f"Topic: {result['topic']}")
    print(f"Questions found: {len(result['questions'])}")
    for q in result['questions']:
        print(f"\n- Level {q['level']}: {q['title']}")
        print(f"  Difficulty: {q['difficulty']}")
        print(f"  Tags: {q['tags']}")
    
    print(f"\nResources: {len(result['resources'])}")
    for r in result['resources']:
        print(f"- [{r['type']}] {r['title']}")
    
    print(f"\nConcept Links: {len(result['concept_links'])}")
    for link in result['concept_links']:
        print(f"- {link['from_concept']} → {link['to_concept']}")
