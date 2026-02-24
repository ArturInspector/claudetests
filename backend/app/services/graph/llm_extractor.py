from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)


class LLMExtractor:
    def __init__(self, llm):
        self._llm = llm

    def build_extraction_prompt(self, question: str, answer: str, topic: str) -> str:
        return f"""
Extract technical concepts from the user's answer below.

**Context:**
- Topic: {topic}
- Question: {question}

**User's Answer:**
{answer}

**Task:**
Identify key technical concepts mentioned or implied in the answer.
For each concept, provide:
1. name: short name (2-5 words)
2. description: brief explanation (1 sentence)
3. confidence: how clearly user understands it (0.0-1.0)
4. mentioned_explicitly: true if directly mentioned, false if implied

**Output Format (JSON only, no markdown):**
{{
  "concepts": [
    {{
      "name": "concept name",
      "description": "brief explanation",
      "confidence": 0.7,
      "mentioned_explicitly": true
    }}
  ]
}}

Return ONLY the JSON, no additional text.
""".strip()

    def build_relationship_prompt(
        self,
        concepts: list[dict[str, Any]],
        answer: str,
    ) -> str:
        concept_names = [c.get("name", c.get("concept_id", "")) for c in concepts]

        return f"""
Analyze relationships between these concepts based on the user's answer.

**Concepts:**
{json.dumps(concept_names, indent=2)}

**User's Answer:**
{answer}

**Task:**
Identify semantic relationships between concepts. Types:
- "prerequisite": concept A must be understood before B
- "similar": concepts are related/analogous
- "opposite": concepts contrast each other
- "example_of": concept A is an example/instance of B
- "component_of": concept A is part of B

**Output Format (JSON only):**
{{
  "relationships": [
    {{
      "from_concept": "concept name",
      "to_concept": "concept name",
      "type": "prerequisite|similar|opposite|example_of|component_of",
      "strength": 0.8,
      "reason": "brief explanation"
    }}
  ]
}}

Return ONLY the JSON, no additional text.
""".strip()

    def parse_llm_response(self, response: str) -> list[dict[str, Any]]:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]

            data = json.loads(cleaned)
            return data.get("concepts", [])
        except json.JSONDecodeError as exc:
            log.error("Failed to parse LLM response as JSON: %s", exc)
            return []

    def parse_relationships_response(self, response: str) -> list[dict[str, Any]]:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start != -1 and end > start:
                    cleaned = cleaned[start:end]

            data = json.loads(cleaned)
            return data.get("relationships", [])
        except json.JSONDecodeError as exc:
            log.error("Failed to parse relationships response: %s", exc)
            return []
